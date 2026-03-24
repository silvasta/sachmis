from collections.abc import Callable
import time

from loguru import logger

from sachmis.config.model import Geminis, Groks, ModelFamily
from sachmis.data import DataManager
from sachmis.utils.print import printer

from .model import Gemini, Grok, Model


def test_data_in_context():
    with DataManager() as data:
        printer(data)
        logger.info("var")
        printer(vars(data))
        logger.info("dir")
        printer(dir(data))


def match_family(data: DataManager, model: ModelFamily, *args, **kwargs):
    """Create instance of execution model from Enum family model"""

    if isinstance(model, Groks):
        return Grok(data, model, *args, **kwargs)

    if isinstance(model, Geminis):
        return Gemini(data, model, *args, **kwargs)


def load_models(
    data: DataManager, models: list[ModelFamily], *args, **kwargs
) -> list[Model]:
    return [
        match_family(data, model, *args, **kwargs)  #
        for model in models
    ]


def launch_models(agents: list[Model], use_async=False, dry_run=False):

    launch_methods: dict[tuple[bool, bool], Callable] = {
        (True, True): launch_dry_run_async,
        (True, False): launch_dry_run_sequential,
        (False, True): launch_async,
        (False, False): launch_sequential,
    }
    launch_methods[(dry_run, use_async)](agents)

    match (use_async, dry_run):
        case (False, False):
            launch_sequential(agents)

        case (True, False):
            launch_async(agents)

        case (False, True):
            launch_dry_run_sequential(agents)

        case (True, True):
            launch_dry_run_async(agents)


# IMPORTANT: tenacity! where to place=??


def launch_sequential(models: list[Model]):
    from tqdm import tqdm

    logger.info("Start of sequential pipeline")

    for model in tqdm(models):
        try:
            model.fire()
        except Exception as e:
            logger.error(f"Problem with model: {model.model.unique}\n{e}")


def launch_dry_run_sequential(models: list[Model]):
    logger.info("DRYRUN - Start of sequential pipeline")
    from tqdm import tqdm

    for model in tqdm(models):
        printer(model.model.api_name)
        logger.debug(model.topic)
        time.sleep(1)


# NOTE: fine so far, maybe replace tqdm


def launch_async(models: list[Model], dry_run=False):
    import asyncio

    # TEST: async behavior and error handling
    from tqdm.asyncio import tqdm

    logger.info("Start of async pipeline")

    # TASK: repair async
    async def thunder(models: list[Model]):
        printer.title(f"Launching Thunder with {len(models)} models")
        tasks: list = [model.fire() for model in models]
        results = await tqdm.gather(*tasks, return_exceptions=True)
        for model, result in zip(models, results):
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
            logger.debug(model.topic)
            await asyncio.sleep(1)

    asyncio.run(thunder(models))
