import time
from loguru import logger

from ..utils.print import printer
from .model import Model
from .data import DataManager
from .gemini import Gemini
from .grok import Grok
from .models import Geminis, Groks, Models


# INFO: main function
def launch_models(
    data: DataManager,
    models: list[Model],
    DRYRUN=False,
    use_async=False,
):
    logger.info("Ready to fire")

    if use_async:
        launch_async(models=models, DRYRUN=DRYRUN)
    else:
        launch_sequential(models=models, DRYRUN=DRYRUN)

    printer.title("Models finished to run, storing data, au revoir!")

    if not DRYRUN:
        data.process_files()
    logger.info("All processes finished")


# TEST: async behavior and error handling
def launch_async(models: list[Model], DRYRUN=False):
    from tqdm.asyncio import tqdm
    import asyncio

    logger.info("Start of async pipeline")

    async def thunder(models: list[Model]):
        printer.thunder(f"Launching Thunder with {len(models)} models")
        if DRYRUN:
            for model in tqdm(models):
                printer.print(model.model.api_name)
                logger.debug(model.topic)
                await asyncio.sleep(1)
        else:
            tasks: list = [model.fire() for model in models]
            results = await tqdm.gather(*tasks, return_exceptions=True)
            for model, result in zip(models, results):
                if isinstance(result, Exception):
                    logger.error(f"Problem with model {model.model.unique}: {result}")
                else:
                    logger.success(f"Model {model.model.unique} successful")

    asyncio.run(thunder(models))


# NOTE: fine so far, maybe replace tqdm
def launch_sequential(models: list[Model], DRYRUN=False):
    from tqdm import tqdm

    logger.info("Start of sequential pipeline")

    for model in tqdm(models):
        if DRYRUN:
            printer.print(model.model.api_name)
            logger.debug(model.topic)
            time.sleep(1)
        else:
            try:
                model.fire()
            except Exception as e:
                logger.error(f"Problem with model: {model.model.unique}\n{e}")


# REFACTOR: make this somehow else
def match_family(data, model, *args, **kwargs):
    """Create instance of execution model from Enum family model"""
    return {
        Groks: Grok,
        Geminis: Gemini,
    }[type(model)](data, model, *args, **kwargs)


# MOVE: only needed for cli? move to cli
def prepare_for_fire(
    data: DataManager,
    raw_models: list[Models],
    fire: bool,
    use_async=False,
    DRYRUN=False,
):
    logger.info("Start of excecution")

    models: list[Model] = [
        *(match_family(data, G) for G in raw_models),
    ]

    if not (fire or confirm_fire(data, models)):
        text = "see you when prompt and command chain is ready!"
        printer.print(text, style="yellow")
        return
    launch_models(data, models, use_async, DRYRUN)


# MOVE: only needed for cli? move to cli
def confirm_fire(data: DataManager, models: list[Model]) -> bool:
    fire = False
    while not fire:
        printer.md("Summary of Release", style="bold red on white", H=1)
        printer.md(data.prompt)

        s = "bold white on cyan"
        printer.print(" Models ", style=s)
        for model in models:
            printer.print(model.model)

        printer.print(" Role ", style=s)
        printer.print(data.role_path)
        printer.md(f"Role: {data.system_role}", style="yellow")

        printer.print(" Files ", style=s)
        for file in data.files:
            printer.print(file.name)

        printer.title("Last check before deployment", style="bold white on red")

        match command := input("type 'ok' to launch, 'r' to reload: "):
            case "ok":
                fire = True
                printer.title("send API request now!", style="green")
            case "r":
                data.load_prompt()
            # TODO: case to adapt role,image,model
            case _:
                logger.debug(f"typed: {command}")
                break
    return fire
