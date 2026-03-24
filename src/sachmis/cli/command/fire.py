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
    PickFiles,
    PickImage,
    PickRole,
)
from sachmis.config.model import ModelFamily
from sachmis.core import capstone as cap
from sachmis.data import DataManager
from sachmis.utils.print import printer

# REFACTOR: everything here below
# - create args and annotations


@logger_catch
def fire(
    # Arguments
    models: Models = None,
    # Options for task selection
    pick_role: PickRole = True,
    files: Files = None,
    pick_files: PickFiles = False,
    images: Images = None,
    pick_image: PickImage = False,
    # General Options
    dry_run: DryRun = False,
    use_async: Async = False,
    direct_fire: Fire = False,  # WARN: test shortcut -fire (collision??)
):
    """Load models and data, assemble prompt and fire a battery"""

    print(f"{models=}")
    print(f"{direct_fire=}")
    print(f"{pick_image=}")

    1 / 0
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
