from contextlib import chdir
from pathlib import Path

from loguru import logger
from sstcore import PathGuard, System, printer

from sachmis.config import SachmisConfig

from ...exceptions import ArborealDataError, SachmisLaunchError
from ..arboreal import ArborealTracker, Biome

# REFACTOR:  where to setup base? data handler? conductor?


def _ensure_base_dir(
    sst: System, base_name: str, root_dir: Path | None = None
):
    base_dir: Path = (root_dir or Path.cwd()) / base_name

    if base_dir != (unique_base_dir := PathGuard.unique(base_dir)):
        # TODO: emit
        sst.printer.danger(f"Detected Folder with new {base_name=}!")
        logger.warning(f"Using: {unique_base_dir=}")
        base_dir: Path = unique_base_dir

    return PathGuard.dir(base_dir)


def create_new_base(sst: System, base_name: str | None = None):
    config: SachmisConfig = sst.config
    config.paths.biome_file()

    # TODO: emit
    logger.info("Create new Base with Forest")

    if (biome_file := config.paths.unconfirmed_biome_file).exists():
        # TODO: emit
        logger.info(f"Attaching new base to Biome: {biome_file.name}")
    else:
        raise ArborealDataError(
            "Biome needed for new Base!", "Biome", biome_file
        )

    if config.paths.inside_camp:
        raise SachmisLaunchError("Already in Base! No new Forest created.")

    base_name: str = base_name or config.names.camp_dir
    base_dir: Path = _ensure_base_dir(sst, base_name)

    try:
        with chdir(base_dir):
            PathGuard.dir(config.names.hidden_dir)
            Path(config.names.prompt).touch()
            # TODO: emit
            printer.success("Files and dirs ready: creating Forest now!")

            forest_file: Path = config.paths.forest_file

            with Biome.edit_mode(config.paths.biome_file()) as biome:
                forest: ArborealTracker = biome.attach_new_forest(forest_file)

    except Exception as error:  # clean up in any case
        # TODO: emit, or raise, PathGuardError?
        logger.error("Failed to create base!")
        PathGuard.remove(base_dir)  # TEST:
        raise error

    # TODO: emit
    logger.info(f"New Base Created: {forest}")  # TODO: ArborealTrackerView
