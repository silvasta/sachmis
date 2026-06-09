import time
from collections.abc import Callable
from contextlib import AbstractContextManager, ExitStack
from typing import Self

from loguru import logger

from ..config import SachmisConfig, get_config
from ..config.models import DummyFamily, Geminis, Groks, ModelFamily
from ..data import DataManager
from ..data.arboreal import ArborealTracker, Forest, Tree
from ..data.files import CampManager
from ..data.handler import FileRollout
from ..utils.print import printer
from .model import Gemini, Grok, Model
from .model.dummy import DummyModel

config: SachmisConfig = get_config()


def match_family(model, data, **kwargs) -> Model:
    """Create instance of execution model from Enum family model"""

    if isinstance(model, Groks):
        data.get_uploader(target=model.target)
        return Grok(model, data, **kwargs)

    if isinstance(model, Geminis):
        data.get_uploader(target=model.target)
        return Gemini(model, data, **kwargs)

    if isinstance(model, DummyFamily):
        return DummyModel(model, data, **kwargs)

    raise ValueError(f"Unknown {model=}")


def launch_models(agents: list[Model], use_async=False, dry_run=False):
    """Pipeline dispatcher"""

    launch_methods: dict[tuple[bool, bool], Callable] = {
        (False, False): launch_sequential,
        (False, True): launch_async,
        (True, False): launch_dry_run_sequential,
        (True, True): launch_dry_run_async,
    }
    launch_methods[(dry_run, use_async)](agents)


def launch_sequential(models: list[Model]):
    from tqdm import tqdm

    logger.info("Start of sequential pipeline")

    for model in tqdm(models):
        try:
            model.assemble_prompt()
            model.fire()
        except Exception as e:
            # TODO: collect exceptions
            logger.error(f"Problem with model: {model.model.unique}\n{e}")


def launch_dry_run_sequential(models: list[Model]):
    logger.info("DRYRUN - Start of sequential pipeline")
    from tqdm import tqdm

    for model in tqdm(models):
        printer(model.model.api_name)
        model.assemble_prompt()
        time.sleep(1)


def launch_async(models: list[Model]):
    import asyncio

    from tqdm.asyncio import tqdm

    logger.info("Start of async pipeline")

    # TASK: repair async

    async def thunder(models: list[Model]):
        printer.title(f"Launching Thunder with {len(models)} models")
        tasks: list = [model.fire() for model in models]
        results = await tqdm.gather(*tasks, return_exceptions=True)
        for model, result in zip(models, results, strict=False):
            model.assemble_prompt()  # WARN: model.assemble_prompt() needed, proper here?
            if isinstance(result, Exception):
                logger.error(
                    f"Problem with model {model.model.unique}: {result}"
                )
            else:
                logger.success(f"Model {model.model.unique} successful")

    asyncio.run(thunder(models))


def launch_dry_run_async(models: list[Model]):
    logger.info("DRYRUN - Start of async pipeline")
    import asyncio

    from tqdm.asyncio import tqdm

    async def thunder(models: list[Model]):
        printer.title(f"Launching {len(models)} models")
        for model in tqdm(models):
            printer(model.model.api_name)
            model.assemble_prompt()
            await asyncio.sleep(1)

    asyncio.run(thunder(models))


class ForestExtractor(AbstractContextManager):
    """Ensure Forest Data is loaded at start and saved at exit"""

    def __init__(self, data: DataManager):

        logger.debug("Loading Forest...")
        self.data: DataManager = data

        with Forest.edit_mode(path := config.paths.forest_file) as forest:
            self.tracker: ArborealTracker = forest.sample_tracker(path)

            self.tree_tracker: ArborealTracker = (
                forest.provide_tree(tree_id)
                if (tree_id := data.handler.scanned_tree_id)
                else forest.attach_new_tree(data.handler.topic)
            )
            data.handler.attach_tracker(self.tree_tracker)

            self.camp: CampManager = forest.get_camp()
            data.attach_camp(self.camp)

        logger.debug("Forest Data extracted - Closing Forest for now...")

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        logger.debug("...Forest Extractor 󱢗")

        if exc_type is not None:  # LATER: what can happen?
            logger.warning(f"Task failed with {exc_type.__name__}")
            return config.defaults.context.forest_error.swallow

        logger.debug("Loading Forest...")
        with Forest.edit_mode(self.tracker.path) as forest:
            forest.attach_camp_back_by_mirror(self.camp)
            # LATER: confirm Tree, maybe after first response is written

        logger.debug("Forest closed - Data transferred back")
        return config.defaults.context.forest_end.swallow


class TreeExtractor(AbstractContextManager):
    """Ensure Tree Data is loaded at start and saved at exit"""

    def __init__(self, data: DataManager):

        logger.debug("Loading Tree...")
        self.data: DataManager = data

        with Tree.edit_mode(path := data.handler.tree_tracker.path) as tree:
            self.tracker: ArborealTracker = tree.sample_tracker(
                path, local_id=data.handler.tree_tracker.local_id
            )
            self.data.handler.attach_tree_data(
                sprout_id=tree.next_sprout_id(),
                full_dag=tree.export_dag(),
            )
        logger.debug("Tree Data extracted - Closing Tree for now...")

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        logger.debug("...Tree Extractor ")

        if exc_type is not None:  # LATER: what can happen?
            logger.warning(f"Task failed with {exc_type.__name__}")
            return config.defaults.context.tree_error.swallow

        logger.debug("Loading Tree...")
        with Tree.edit_mode(self.tracker.path) as tree:
            tree.attach_to_dag(self.data.handler.export_dag())

        logger.debug("Tree closed - Data transferred back")
        return config.defaults.context.tree_end.swallow


class Fire(AbstractContextManager):
    def __init__(self):
        self.stack: ExitStack = ExitStack()
        self.agents: list[Model] = []

    def __enter__(self) -> Self:
        self.data: DataManager = self.stack.enter_context(
            DataManager(handler=FileRollout())
        )
        self.forest: ForestExtractor = self.stack.enter_context(
            ForestExtractor(self.data)
        )
        logger.info("ForestExtractor: Stacked to Context")

        self.tree: TreeExtractor = self.stack.enter_context(
            TreeExtractor(data=self.data)
        )
        logger.info("TreeExtractor: Stacked to Context")

        logger.success("capstone.Fire session is ready")
        return self

    def load_models(self, models: list[ModelFamily]) -> list[Model]:
        logger.info(f"Start of loading: {models=}")

        self.agents: list[Model] = [
            match_family(model, self.data) for model in models
        ]
        return self.agents

    def launch(self, use_async=False, dry_run=False):
        launch_models(self.agents, use_async, dry_run)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # When the 'with CapSession()' block in your CLI finishes,
        # ExitStack automatically pops and triggers __exit__ for everything it holds:
        # 1. TreeConductor.__exit__() runs -> Attaches your trees safely.
        # 2. DataManager.__exit__() runs -> Closes out the main data.
        return self.stack.__exit__(exc_type, exc_val, exc_tb)
