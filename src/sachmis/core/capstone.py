import time
from collections.abc import Callable
from contextlib import AbstractContextManager, ExitStack
from pathlib import Path
from typing import Self

from loguru import logger

from ..config.model import Geminis, Groks, ModelFamily
from ..config.model.dummy import DummyFamily
from ..data import DataManager, Prompt
from ..data.arboreal import ArborealTracker, Forest, Tree
from ..data.conversation.prompt import PromptData
from ..data.files import CampManager
from ..data.handler import FileRollout
from ..utils.print import printer
from .model import Gemini, Grok, Model
from .model.dummy import DummyModel


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


class ExtractFromForest(AbstractContextManager):
    def __init__(
        self, forest_file: Path, tree_id: int, raw_prompt: PromptData
    ):

        with Forest.edit_mode(forest_file) as forest:
            self.tracker: ArborealTracker = forest.sample_tracker(forest_file)
            self.tree_tracker: ArborealTracker = forest.provide_tree(
                tree_id, raw_prompt
            )
            # TODO: find prompt ancestor
            self.camp: CampManager = forest.get_camp()

        self.path: Path = forest_file

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        if exc_type is not None:
            logger.warning(f"Task failed with {exc_type.__name__}")
            return False

        with Forest.edit_mode(self.path) as forest:
            printer(forest)
            # TODO: return Camp
            # TODO: confirm Tree

        return False


class ExtractFromTree(AbstractContextManager):
    def __init__(self, tree_file: Path):

        with Tree.edit_mode(tree_file) as tree:
            self.tracker: ArborealTracker = tree.sample_tracker(tree_file)
            # TODO: attach prompt, extract
            # TODO: previous_sprout

        self.path: Path = tree_file

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        if exc_type is not None:
            logger.warning(f"Task failed with {exc_type.__name__}")
            return False

        with Tree.edit_mode(self.path) as tree:
            printer(tree)
            # TODO: modify Prompt
            # TODO: attach Response
            # TODO: test consistency?
            self.prompt: Prompt = tree.root_prompt  # WARN:

        return False


class Fire(AbstractContextManager):
    def __init__(self):
        self.stack: ExitStack = ExitStack()
        self.agents: list[Model] = []

    def __enter__(self) -> Self:
        # Push to stack, DataManager will close with FireSession
        self.data: DataManager = self.stack.enter_context(
            DataManager(biome=True, forest=True)
        )
        self.rollout = FileRollout()  # MOVE: maybe into data

        self.forest_handler: ExtractFromForest = self.stack.enter_context(
            ExtractFromForest(
                self.data.forest_file,
                tree_id=self.rollout.tree_id,
                raw_prompt=self.rollout.load_raw_prompt(),
            )
        )
        logger.info("Forest Extractor stacked to Context")
        self.data.attach_camp(self.forest_handler.camp)

        self.tree_handler: ExtractFromTree = self.stack.enter_context(
            ExtractFromTree(tree_file=self.forest_handler.tree_tracker.path)
        )
        logger.info("Tree Extractor stacked to Context")
        self.data.attach_prompt(self.tree_handler.prompt)
        self.rollout.attach_prompt(self.tree_handler.prompt)

        logger.success("capstone.Fire ready for session")

        return self

    def load_models(self, models: list[ModelFamily]) -> list[Model]:
        logger.info(f"Start of loading: {models=}")

        self.agentgs: list[Model] = [
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
