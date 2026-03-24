from boltons.iterutils import unique
from pathlib import Path

from loguru import logger
from silvasta.utils.path import PathGuard

from sachmis.config.manager import config
from sachmis.utils.print import printer

from .arboreal import Biome, Forest, Sprout, Tree

# NEXT: bring in the new arboreal


class DataManager:
    """Loads Pydantic models on entry, saves them on clean exit."""

    def __init__(self, save_at_exit=True):  # TODO: assign task

        self.save_at_exit: bool = save_at_exit

        if config.paths.biome_file.exists():
            logger.info("Biome file exists")
        else:
            logger.warning("Biome file not found, create new?")
            # TODO: create biome here? wait for task!

        if config.paths.in_base:
            logger.info("Current location in base")

            if config.paths.forest_file.exists():
                logger.info("Forest file exists")
            else:
                logger.warning(f"Not found:{config.paths.forest_file=}")

            self.in_forest = True
        else:
            self.in_forest = False

    def __enter__(self) -> "DataManager":
        logger.info("DataManager: Load data in context")

        self.biome: Biome = Biome.load_state()

        self.check_health_biome()  # INFO: so far: pass

        if self.in_forest:
            # LATER: open multiple forest
            self.forest: Forest = Forest.load_state()

        return self

    def __exit__(self, exception_type, exception_value, exception_trace_back):
        # LATER: decide how to handle which error

        if not self.save_at_exit:
            logger.info("DataManager: Close intended without saving")
            return

        logger.info("DataManager: Close data from context")

        if exception_type is not None:
            logger.error(f"DataManager - Error: ({exception_type.__name__})")
            logger.warning("State not saved!")

            if issubclass(exception_type, ValueError):
                # INFO: example error handling
                logger.info(f"Harmless UI Error: {exception_value=}")
                logger.warning("State not saved!")

                # Surpress exception (after handling it here)
                return True

        if self.in_forest:
            # LATER: close multiple forest
            self.forest.save_state()

        self.biome.save_state()

        logger.info("DataManager: Clean Exit")

        # Propagate exception to caller
        return False

    def check_health_biome(self):
        # TODO: handle dublicates, other health tests?
        DataManager._check_dublicated_biome_files()
        self.biome._prune_dublicated_forest_paths()
        self.biome._check_active_forest_paths()

    @staticmethod  # LATER: cls or self? how to handle multiple biomes?
    def _check_dublicated_biome_files():
        biome_files: list[Path] = PathGuard.find_sequence(
            config.paths.biome_file
        )
        num_biome_files: int = len(biome_files)
        logger.info(f"For current biome path: {num_biome_files=}")

        logger.debug(f"current status: {biome_files=}")
        if num_biome_files > 1:
            for file in biome_files:
                printer(file)

    @classmethod
    def create_new_biome(cls, name: str | None = None):
        logger.info("Create new Biome")
        Biome().save_state(
            biome_file=PathGuard.unique(config.paths.biome_file)
        )  # PathGuard.unique or not allow new Biome() if file exists
        DataManager._check_dublicated_biome_files()

    @classmethod
    def create_new_base(cls, base_name: str | None = None):
        logger.info("Create new Base with Forest")

        with cls() as data:
            if data.in_forest:
                logger.error("Already in Base! No new Forest will be created.")
                return

            if base_name is None:
                base_name: str = config.names.base_dir

            base_dir_unconfirmed = Path.cwd() / base_name
            base_dir_unique: Path = PathGuard.unique(base_dir_unconfirmed)
            base_dir: Path = PathGuard.dir(base_dir_unique)
            # MOVE: that somehow into PathGuard?
            # pros: - 1 single step for multiple actions
            # cons: - maybe to specified for a general class
            # - warnings need to be done anyway here (or CLI)
            if base_dir_unconfirmed != base_dir:
                printer.warn(f"Detected Folder with new {base_name=}!")
                logger.warning(f"Using: {base_dir_unique=}")

            promp_path: Path = base_dir / config.names.prompt
            PathGuard.file(promp_path, default_content="", raise_error=False)

            camp_name: str = config.names.camp_dir
            camp_dir: Path = PathGuard.dir(base_dir / camp_name)

            forest_file: Path = camp_dir / config.names.forest_file

            # TODO: local structure in camp
            # - config file(s)?
            # - roles?
            # - etc..

            printer.success("Files and dirs ready: creating Forest now!")

            forest = Forest()
            forest.save_state(forest_file)

            data.biome.forests.append(forest_file)

        logger.info(f"New base created at:\n{base_dir}")

    def load_local_files_to_forest(self, clear_current_files=False):
        """Browse local files folder in camp and attach files to Forest"""

        self.forest.load_local_files(
            # LATER: sort! by folder/section? check with shmoodle
            from_empty_status=clear_current_files,
        )
