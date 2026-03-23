from pathlib import Path
from typing import Annotated

import typer
from loguru import logger
from silvasta.cli.setup import logger_catch

from sachmis.config.model import Geminis, Groks, ModelFamily
from sachmis.core import capstone as cap
from sachmis.data import DataManager
from sachmis.utils.print import printer

# REFACTOR: everything here below
# - create args and annotations


@logger_catch
def fire(
    ctx: typer.Context,
    # - - - Direct Release - - - #
    fire: Annotated[
        bool,
        typer.Option(
            "--fire",
            help="Avoid confirmation step before API call",
        ),
    ] = False,
    # - - - xAI Grok Models - - - #
    xai_models: Annotated[
        list[Groks] | None,
        typer.Option(
            "--xai",
            "-x",
            help="Grok model(s)",
        ),
    ] = None,
    # - - - File paths - - - #
    files: Annotated[
        # HACK: pick from list of uploaded files!
        # TODO: update local and online file registry with new file path
        list[str] | None,
        typer.Option(
            "--file",
            "-f",
            # WARN: possibly non unique
            help="file names of file in local file registry",
        ),
    ] = None,
    # - - - Google Gemini Models - - - #
    google_models: Annotated[
        list[Geminis] | None,
        typer.Option(
            "--google",
            "-g",
            help="Gemini model(s)",
        ),
    ] = None,
    # - - - Model Picker - - - #
    pick_model: Annotated[
        bool,
        typer.Option(
            "--pick-model",
            "-m",  # NOTE: picker for model
            help="Pick model(s) Overrides other model selections!",
        ),
    ] = False,
    # - - - Image Paths - - - #
    images: Annotated[
        list[Path] | None,
        typer.Option(
            "--images",
            "-i",
            help="Add image(s) to prompt",
        ),
    ] = None,
    # - - - Image Picker - - - #
    pick_image: Annotated[
        bool,
        typer.Option(
            "--pick-image",
            "-I",  # NOTE: picker for image
            help="Pick image(s) from cwd",
        ),
    ] = False,
    # - - - Role Picker - - - #
    role: Annotated[
        bool,
        typer.Option(
            "--pick-role",
            "-r",  # NOTE: picker for role
            help="Avoid confirmation step before API call",
        ),
    ] = False,
    # - - - Async - - - #
    use_async: Annotated[
        bool,
        typer.Option(
            "--use-async",
            "-a",
            help="Send all models together with async",
        ),
    ] = False,
    # - - - DRYRUN - - - #
    DRYRUN: Annotated[
        bool,
        typer.Option(
            "--dry",
            help="Just simulate pipeline without online requests",
        ),
    ] = False,
):
    """Load models and data, assemble prompt and fire a battery"""

    data: DataManager = ctx.obj["data"]
    data.load_forest()
    data.load_prompt()

    printer.title("Preparing Models...", style="Title")
    models: list[ModelFamily] = [
        *(xai_models or []),
        *(google_models or []),
        # *(picked_models() if pick_model else []),
    ]
    logger.debug(f"loading {len(models)=}")
    printer.md(f"...{len(models)=} selected for pipeline")

    if not (len(models) > 0):
        logger.error(f"launching {len(models)=} makes no sense...")
        return

    # NOTE: refactor this, only model here, rest hidden in data, like pick_role

    printer.title("Preparing Images...", style="Title")
    images: list[Path] = [
        *(images or []),
        # *(picked_images() if pick_model else []),
    ]
    data.prepare_images(images)
    logger.debug(f"appending {len(images)=}")
    printer.md(f"...{len(images)} images selected for pipeline")

    if files is not None:
        data.prepare_files(files)

    logger.debug(f"appending {len(data.files)=}")
    printer.md(f"...{len(data.files)} files selected for pipeline")

    # TODO: google files (uploaded)

    data.load_system_role()

    cap.prepare_for_fire(
        data,
        models,
        fire,
        use_async,
        DRYRUN,
    )
