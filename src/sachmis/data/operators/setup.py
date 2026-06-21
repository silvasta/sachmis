import shutil
from contextlib import chdir
from pathlib import Path

from loguru import logger
from sstcore.utils import PathGuard

from ..config import config
from ..exceptions import ArborealFileMissingError
from ..utils.print import printer
from .arboreal import ArborealTracker, Biome

# REFACTOR:  where to setup base? data handler? conductor?


def _ensure_base_dir(base_name: str, root_dir: Path | None = None):
    base_dir: Path = (root_dir or Path.cwd()) / base_name

    if base_dir != (unique_base_dir := PathGuard.unique(base_dir)):
        printer.danger(f"Detected Folder with new {base_name=}!")
        logger.warning(f"Using: {unique_base_dir=}")
        base_dir: Path = unique_base_dir

    return PathGuard.dir(base_dir)


def create_new_base(base_name: str | None = None):
    logger.info("Create new Base with Forest")

    if (biome_file := config().paths.unconfirmed_biome_file).exists():
        logger.info(f"Attaching new base to Biome: {biome_file.name}")
    else:
        logger.error("Biome needed for new Base!")
        logger.error("Check: sachmis biome {setup | show | select}")
        raise ArborealFileMissingError("Biome", biome_file)

    if config().paths.in_forest:
        logger.error("Already in Base! No new Forest will be created.")
        return

    base_name: str = base_name or config().names.base_dir
    base_dir: Path = _ensure_base_dir(base_name)

    try:
        with chdir(base_dir):
            PathGuard.dir(config().names.camp_dir)
            Path(config().names.prompt).touch()
            printer.success("Files and dirs ready: creating Forest now!")

            forest_file: Path = config().paths.forest_file

            with Biome.edit_mode(config().paths.biome_file()) as biome:
                forest_tracker: ArborealTracker = biome.attach_new_forest(
                    forest_file
                )

    except Exception as error:  # clean up in any case
        logger.error("Failed to create base!")
        shutil.rmtree(base_dir)
        raise error

    logger.info(  # TODO: stat print instead of full tracker
        f"New Base Created: {forest_tracker=}"
    )
