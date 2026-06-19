import time
from collections.abc import Callable

from loguru import logger

from ...utils import printer
from .agent import Model


def models(agents: list[Model], use_async=False, dry_run=False):
    """Dispatch and launch Models by Pipeline"""

    launch_methods: dict[tuple[bool, bool], Callable] = {
        (False, False): sequential_pipeline,
        (False, True): async_pipeline,
        (True, False): dry_run_sequential_pipeline,
        (True, True): dry_run_async_pipeline,
    }
    launch_methods[(dry_run, use_async)](agents)


def sequential_pipeline(models: list[Model]):
    """Launch Sequential Pipeline"""

    logger.info("Start of sequential pipeline")

    from tqdm import tqdm

    for model in tqdm(models):
        try:
            model.assemble_prompt()
            model.fire()
        except Exception as e:
            logger.error(
                f"Problem with {model}:"
                f"{model.model.unique} caused {type(e)}, details:\n{e}"
            )


def dry_run_sequential_pipeline(models: list[Model]):
    """Launch dry-run for sequential pipeline"""

    logger.info("DRYRUN - Start of sequential pipeline")

    from tqdm import tqdm

    for model in tqdm(models):
        printer(model.model.api_name)
        model.assemble_prompt()
        time.sleep(1)


def async_pipeline(models: list[Model]):
    """Launch Async Pipeline"""

    logger.info("Start of async pipeline")

    import asyncio

    from tqdm.asyncio import tqdm

    async def pipeline(models: list[Model]):
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

    asyncio.run(pipeline(models))


def dry_run_async_pipeline(models: list[Model]):
    """Launch dry-run for async pipeline"""

    logger.info("DRYRUN - Start of async pipeline")

    import asyncio

    from tqdm.asyncio import tqdm

    async def pipeline(models: list[Model]):
        printer.title(f"Launching {len(models)} models")
        for model in tqdm(models):
            printer(model.model.api_name)
            model.assemble_prompt()
            await asyncio.sleep(1)

    asyncio.run(pipeline(models))
