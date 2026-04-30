import time
from collections.abc import Callable

from loguru import logger

from sachmis.config.defaults import GeminiParam, GrokParam, ModelParam

from ..config.model import Geminis, Groks, ModelFamily
from ..config.model.dummy import DummyFamily
from ..data import DataManager
from ..data.arboreal import ArborealTracker, Forest, Sprout, Tree
from ..utils.print import printer
from .model import Gemini, Grok, Model
from .model.dummy import DummyModel


def match_family(model, **kwargs) -> Model:
    """Create instance of execution model from Enum family model"""

    if isinstance(model, Groks):
        if "param" not in kwargs:
            kwargs |= GrokParam()
            printer(kwargs)
        return Grok(model, **kwargs)

    if isinstance(model, Geminis):
        if "param" not in kwargs:
            kwargs |= GeminiParam()
            printer(kwargs)
        return Gemini(model, **kwargs)

    if isinstance(model, DummyFamily):
        if "param" not in kwargs:
            kwargs["param"] = ModelParam()
            printer(kwargs)
        return DummyModel(model, **kwargs)

    raise ValueError(f"Unknown {model=}")


def load_models(data: DataManager, models: list[ModelFamily]) -> list[Model]:
    logger.info(f"Start of loading: {models=}")

    tree_tracker: list[ArborealTracker] = []

    with Forest.edit_mode(data.forest_file) as forest:
        logger.info("Loading Forest and extract Trees")
        for model in models:
            tree_tracker.append(  # NEXT: info from data
                forest.provide_tree(model=model.unique, prompt=data._prompt)
            )
    logger.info("Trees extracted, closing Forest during task")

    sprouts: list[Sprout] = []

    for model, tree in zip(models, tree_tracker, strict=True):
        with Tree.edit_mode(tree.path) as tree:
            sprouts.append(  # NEXT: info from data, LOCATOR
                tree.provide_sprout(model=model.unique, prompt=data._prompt)
            )
    logger.info("Sprouts extracted, closing Trees during task")

    trees: list[Tree] = [Tree.read_mode(t.path) for t in tree_tracker]
    # LATER: optimize how this works, Trees openend for 3th time here...

    attached_models: list[Model] = [
        match_family(model, data=data, tree=tree, sprout=sprout)
        for model, tree, sprout in zip(models, trees, sprouts, strict=True)
    ]

    return attached_models


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


# NOTE: fine so far, maybe replace tqdm


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
