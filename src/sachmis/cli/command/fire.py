from sachmis.core.model.agent import Model
from pathlib import Path

from loguru import logger
from silvasta.cli.setup import logger_catch

from sachmis.cli.args import (
    Async,
    DryRun,
    Files,
    Fire,
    Images,
    Models,
    PickFile,
    PickImage,
    PickRole,
)
from sachmis.config.model import ModelFamily
from sachmis.core import capstone as cap
from sachmis.data import DataManager
from sachmis.utils.parse import (
    reversed_name_from_unique,
)
from sachmis.utils.picker import pick_files, pick_images, pick_models
from sachmis.utils.print import printer


@logger_catch
def fire(
    # Arguments
    models: Models = None,
    # Options for task selection
    pick_role: PickRole = True,
    files: Files = None,
    pick_file: PickFile = False,
    images: Images = None,
    pick_image: PickImage = False,
    # General Options
    use_async: Async = False,
    dry_run: DryRun = False,
    direct_fire: Fire = False,
):
    """Load models and data, assemble prompt and fire"""

    # INFO: start data context here because of priority of execution:
    # - loading models and prompt before picking files and images
    # - model/prompt failures should not cause unnecessary picks

    with DataManager() as data:
        data.load_prompt()

        models: list[ModelFamily] = _prepare_model_args(models)
        agents: list[Model] = cap.load_models(data, models)

        files: list[Path] = _prepare_file_args(files, pick_file)
        images: list[Path] = _prepare_image_args(images, pick_image)

        role: Path | None = _prepare_role(pick_role)
        data.load_system_role()

        if not fire and not confirm_fire(data, agents):
            printer.yellow("see you when prompt and command chain is ready!")
            return

        logger.info("Ready to fire")

        cap.launch_models(agents, use_async, dry_run)

        # TODO: ensure data is save

        printer.title("Models finished to run, storing data, au revoir!")

    logger.info("All processes finished")


def confirm_fire(data: DataManager, models: list[Model], fire=False) -> bool:

    # TASK: style concept for entire printer story

    while not fire:
        # TODO: show this once for input arg fire=True?

        printer.title(
            "Summary of Release",
            style="bold green on white",
        )
        printer.md(data.prompt)  # TODO:

        printer.preview(
            title="Models",
            lines=[model.model for model in models],
        )

        printer.preview(
            title="Role",
            lines=[data.role_path],
        )
        printer.md(f"Role: {data.system_role}", style="yellow")  # TODO:

        printer.preview(
            title="Files",
            lines=[file.name for file in data.files],
        )

        printer.preview(
            title="Images",
            lines=[image.name for image in data.img],
        )

        printer.aware("Last check before deployment")

        match input("type 'ok' to launch, 'r' to reload: "):
            case "ok":
                fire = True
                printer.title("send API request now!", style="green")
            case "r":
                # TODO: case to adapt role,image,model? probably not! either remove r
                data.load_prompt()
            case _:
                break

    return fire


def _prepare_model_args(models: list[str] | None) -> list[ModelFamily]:

    printer.title("Preparing Models...", style="Title")

    models: list[ModelFamily] = (
        [
            parsed_model
            for model_unique in models
            if (parsed_model := reversed_name_from_unique(model_unique))
            is not None
        ]
        if models is not None
        else pick_models()
    )
    logger.debug(f"loading {len(models)=}")

    if not models:
        raise AttributeError("No valid models parsed from input...")

    printer.md(f"...{len(models)=} selected for pipeline")

    return models


def _prepare_file_args(
    files: list[Path] | None, pick_file: bool
) -> list[Path]:

    printer.title("Preparing Files...", style="Title")

    files: list[Path] = [
        *(files or []),
        *(pick_files() if pick_file else []),
    ]
    logger.debug(f"appending {len(files)=}")

    for file in files:
        if not file.exists():
            raise AttributeError(f"Invalid {file=}")

    printer.md(f"...{len(files)} files selected for pipeline")

    return files


def _prepare_image_args(
    images: list[Path] | None, pick_image: bool
) -> list[Path]:

    printer.title("Preparing Images...", style="Title")

    images: list[Path] = [
        *(images or []),
        *(pick_images() if pick_image else []),
    ]
    logger.debug(f"loading {len(images)=}")

    for image in images:
        if not image.exists():
            raise AttributeError(f"Invalid {image=}")

    printer.md(f"...{len(images)} images selected for pipeline")

    return images


def _prepare_role(pick_role: bool) -> Path | None:

    raise NotImplementedError
