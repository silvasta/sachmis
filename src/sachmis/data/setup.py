from sachmis.utils import ArborealFileMissingError
import shutil
from contextlib import chdir
from pathlib import Path

from loguru import logger
from silvasta.utils import PathGuard

from sachmis.config import SachmisConfig, get_config
from sachmis.data.files import CampManager
from sachmis.utils.exceptions import SachmisError
from sachmis.utils.print import printer

from .arboreal import ArborealTracker, Biome


def create_new_biome(name: str | None = None) -> Path:
    # NEXT: setup automatic if not found
    config: SachmisConfig = get_config()
    logger.info("Create new Biome")

    biome_filename: str = config.names.biome_file if name is None else name

    biome_file: Path = config.paths.new_biome_file(biome_filename)

    if name is None:
        config.names.biome_file: str = biome_file.name
        config.save_settings()  # MOVE: 3er block to config?
        logger.info(f"Updated active Biome in Names: {biome_file=}")

    Biome().save_state(file=biome_file, lock_required=False)

    return biome_file


def check_biome_files():
    config: SachmisConfig = get_config()
    biome_files: set[Path] = config.paths.biome_files

    # MERGE: with cli.biome.select

    if num_biome_files := len(biome_files) > 1:
        logger.info(f"Found {num_biome_files=} in {config.paths.biome_dir=}")
        for file in biome_files:
            printer(file)
        logger.debug(f"current status: {biome_files=}")
    else:
        logger.debug(f"current status: 1 {biome_files=}")


@PathGuard.dir
def _ensure_base_dir(base_name: str, root_dir: Path | None = None):
    base_dir: Path = (root_dir or Path.cwd()) / base_name

    if base_dir != (unique_base_dir := PathGuard.unique(base_dir)):
        printer.danger(f"Detected Folder with new {base_name=}!")
        logger.warning(f"Using: {unique_base_dir=}")
        base_dir: Path = unique_base_dir

    return base_dir


def create_new_base(base_name: str | None = None):
    config: SachmisConfig = get_config()
    logger.info("Create new Base with Forest")

    if (biome_file := config.paths.unconfirmed_biome_file).exists():
        logger.info(f"Attaching new base to Biome: {biome_file.name}")
    else:
        logger.error("Biome needed for new Base!")
        logger.error("Check: sachmis biome {setup | show | select}")
        raise ArborealFileMissingError("Biome", biome_file)

    if config.paths.in_forest:  # LATER: Forest in Forest? desired?
        logger.error("Already in Base! No new Forest will be created.")
        return

    base_name: str = base_name or config.names.base_dir
    base_dir: Path = _ensure_base_dir(base_name)

    try:
        with chdir(base_dir):
            PathGuard.dir(config.names.camp_dir)
            Path(config.names.prompt).touch()
            camp: CampManager = CampManager()
            printer.success("Files and dirs ready: creating Forest now!")

            forest_file: Path = config.paths.forest_file

        with Biome.edit_mode(config.paths.biome_file) as biome:
            forest_tracker: ArborealTracker = biome.attach_new_forest(
                forest_file, camp
            )

    except Exception as error:  # clean up in any case
        logger.error("Failed to create base!")
        shutil.rmtree(base_dir)
        raise error

    logger.info(f"New Base Created: {forest_tracker=}")
