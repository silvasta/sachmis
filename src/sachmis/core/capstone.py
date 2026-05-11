import time
from collections.abc import Callable
from contextlib import AbstractContextManager, ExitStack
from typing import Self

from loguru import logger

from ..config.model import Geminis, Groks, ModelFamily
from ..config.model.dummy import DummyFamily
from ..data import DataManager
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


# def load_models(data: DataManager, models: list[ModelFamily]) -> list[Model]:
#     logger.info(f"Start of loading: {models=}")
#
#     tree_tracker: list[ArborealTracker] = []
#
#     # INFO: this will most likely change
#     with Forest.edit_mode(data.forest_file) as forest:
#         logger.info("Load Forest and extract Trees")
#         for model in models:
#             tree_tracker.append(
#                 forest.attach_new_tree(model=model.unique, prompt=data.prompt)
#                 if data._next_fs_locator == 0
#                 else forest.provide_tree(previous_sprout=data._previous_sprout)
#             )
#         data.load_camp(forest)
#
#     logger.info("Trees extracted, close and unlock Forest during task")
#
#     sprouts: list[Sprout] = []
#
#     # IMPORTANT: here is the last remaining thing to solve:
#
#     # - Ensure any Tree that is opened gets opened and attached again
#     # - Optional, clean up if task failed
#     for model, tracker in zip(models, tree_tracker, strict=True):
#         sprout: Sprout = Tree.extract_sprout(
#             tree_file=tracker.path,
#             previous_sprout=data._previous_sprout,
#             model=model.unique,
#             prompt=data.prompt,
#         )
#         data.track_extracted_sprout(sprout, tree_tracker=tracker)
#         logger.debug(f"extracted from Tree: {sprout.unique_id=}")
#         sprouts.append(sprout)
#
#     logger.info("Sprouts extracted, close and unlock Trees during task")
#
#     attached_models: list[Model] = [
#         match_family(model, data=data, sprout=sprout)
#         for model, sprout in zip(models, sprouts, strict=True)
#     ]
#
#     return attached_models


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


# class TreeConductor(AbstractContextManager):
#     def __init__(self, data: DataManager):
#         self.data: DataManager = data
#         self.tracked_sprouts = []  # Memory for the 5-minute gap
#         # NEXT: open and check trees
#
#     def extract_all(self, models, tree_trackers):
#         """Phase 1: Open, extract, and close immediately."""
#         # REMOVE:
#         sprouts = []
#         for model, tracker in zip(models, tree_trackers, strict=True):
#             sprout = Tree.extract_sprout(
#                 tree_file=tracker.path,
#                 previous_sprout=self.data._previous_sprout,
#                 model=model.unique,
#                 prompt=self.data.prompt,
#             )
#             self.data.track_extracted_sprout(sprout, tree_tracker=tracker)
#             logger.debug(f"extracted from Tree: {sprout.unique_id=}")
#
#             sprouts.append(sprout)
#
#             # Store the state so we know what to attach later!
#             self.tracked_sprouts.append((tracker, sprout))
#
#         return sprouts
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         """Phase 2: The task finished (or crashed). Re-open and process."""
#         if exc_type is None:
#             # TODO: handle fail, handle new tree, hanlde existing tree
#             logger.info("Task successful. Re-opening Trees to attach results.")
#             for tracker, sprout in self.tracked_sprouts:
#                 # 1. Re-open the tree file (fetching any changes from other terminals)
#                 # 2. Attach the finished data
#                 # 3. Close it
#                 with Tree.edit_mode(tracker.path) as tree:
#                     tree.attach_finished_sprout(sprout)
#         else:
#             logger.warning(
#                 f"Task failed with {exc_type.__name__}. Rolling back Trees."
#             )
#             for tracker, sprout in self.tracked_sprouts:
#                 # Perform any cleanup/rollback logic here if needed
#                 pass
#
#         return False  # Let exceptions bubble up


class Fire(AbstractContextManager):
    def __init__(self):
        self.stack: ExitStack = ExitStack()
        self.agents: list[Model] = []

    def __enter__(self) -> Self:
        # Push to stack, DataManager will close with FireSession
        self.data: DataManager = self.stack.enter_context(
            DataManager(biome=True, forest=True)
        )
        self.data.load_prompt()
        self.data.load_camp()  # context
        self.data.load_rollout()  # context
        return self

    def load_models(self, models: list[ModelFamily]) -> list[Model]:
        logger.info(f"Start of loading: {models=}")

        # TASK: ensure all trees ready (most likely no load here)
        # tree_conductor: TreeConductor = self.stack.enter_context(
        #     TreeConductor(self.data)
        # )

        self.models: list[Model] = [
            match_family(model, self.data) for model in models
        ]
        return self.models

    def launch(self, use_async=False, dry_run=False):
        """The 1-5 minute task"""
        # This is your current cap.launch_models logic
        launch_models(self.agents, use_async, dry_run)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # When the 'with CapSession()' block in your CLI finishes,
        # ExitStack automatically pops and triggers __exit__ for everything it holds:
        # 1. TreeConductor.__exit__() runs -> Attaches your trees safely.
        # 2. DataManager.__exit__() runs -> Closes out the main data.
        return self.stack.__exit__(exc_type, exc_val, exc_tb)
