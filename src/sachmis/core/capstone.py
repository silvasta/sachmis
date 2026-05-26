import time
from collections.abc import Callable
from contextlib import AbstractContextManager, ExitStack
from typing import Self

from loguru import logger

from sachmis.data.conversation import ConversationBag

from ..config import SachmisConfig, get_config
from ..config.model import Geminis, Groks, ModelFamily
from ..config.model.dummy import DummyFamily
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
    def __init__(self, data: DataManager):

        logger.debug("Loading Forest...")
        with Forest.edit_mode(path := data.forest_file) as forest:
            self.tracker: ArborealTracker = forest.sample_tracker(path)
            tree_tracker: ArborealTracker = forest.provide_tree(
                data.handler.tree_id, data.handler.raw_prompt
            )
            data.handler.attach_tracker(
                tracker=tree_tracker, extracted_from="forest"
            )
            self.camp: CampManager = forest.get_camp()
            data.attach_camp(self.camp)
        logger.debug("Data extracted - Forest closed")

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        logger.debug("...Forest Extractor 󱢗")
        if exc_type is not None:
            logger.warning(f"Task failed with {exc_type.__name__}")
            return config.defaults.context.forest_error.swallow

        logger.debug("Loading Forest...")
        with Forest.edit_mode(self.tracker.path) as forest:
            forest.attach_camp_back_by_mirror(self.camp)
            # LATER: confirm Tree, maybe after first response is written

        logger.debug("Forest closed - Data transfered back")
        return config.defaults.context.forest_end.swallow


class ExtractFromTree(AbstractContextManager):
    def __init__(self, data: DataManager):
        self.data: DataManager = data

        logger.debug("Loading Tree...")
        with Tree.edit_mode(path := data.handler.tree_tracker.path) as tree:
            self.tracker: ArborealTracker = tree.sample_tracker(
                path, local_id=data.handler.tree_tracker.local_id
            )
            cwd_conversations: ConversationBag = (
                tree.find_conversation_by_stem(
                    stems=data.handler.existing_conversations
                )
            )
            cwd_conversations.log_and_print()
            # TODO: attach prompt, extract
            # TODO: previous_sprout
            # TODO: find prompt ancestor

        logger.debug("Data extracted - Tree closed")
        data.handler.attach_tracker(
            tracker=self.tracker, extracted_from="forest"
        )

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        logger.debug("...Tree Extractor ")
        if exc_type is not None:
            logger.warning(f"Task failed with {exc_type.__name__}")
            return config.defaults.context.tree_error.swallow

        logger.debug("Loading Tree...")
        with Tree.edit_mode(self.tracker.path) as tree:
            printer(tree)
            # TODO: modify Prompt
            # TODO: attach Response
            # TODO: test consistency?

        logger.debug("Tree closed - Data transfered back")
        return config.defaults.context.tree_end.swallow


class Fire(AbstractContextManager):
    def __init__(self):
        self.stack: ExitStack = ExitStack()
        self.agents: list[Model] = []

    def __enter__(self) -> Self:
        # Push to stack, DataManager will close with FireSession
        self.data: DataManager = self.stack.enter_context(
            DataManager(biome=True, forest=True)
        )
        self.data.attach_handler(FileRollout())

        self.forest_handler: ExtractFromForest = self.stack.enter_context(
            ExtractFromForest(self.data)
        )
        logger.info("Forest Extractor stacked to Context")

        self.tree_handler: ExtractFromTree = self.stack.enter_context(
            ExtractFromTree(data=self.data)
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
