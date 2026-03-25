from pathlib import Path

from boltons.strutils import slugify
from loguru import logger
from silvasta.utils.path import PathGuard

from sachmis.config.manager import config
from sachmis.config.model.family import ModelFamily
from sachmis.data.files import Prompt, UploadFile
from sachmis.utils.print import printer

from .arboreal import Biome, Forest, Sprout, Tree


class DataManager:
    """Loads Pydantic models on entry, saves them on clean exit."""

    def __init__(self, save_at_exit=True, forest_required=False):

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

        if forest_required and not self.in_forest:
            # LATER: personalized exception, NotInForestError?
            raise FileNotFoundError("Not in Forest!")

    def __enter__(self) -> "DataManager":
        logger.info("DataManager: Load data in context")

        self.biome: Biome = Biome.load_state()

        self.check_health_biome()

        if self.in_forest:
            self.forest: Forest = Forest.load_state()
            # LATER: open multiple forest

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
            self.forest.save_state()
            # LATER: close multiple forest

        self.biome.save_state()

        logger.info("DataManager: Clean Exit")

        # Propagate exception to caller
        return False

    def check_health_biome(self):
        DataManager._check_dublicated_biome_files()
        self.biome._prune_dublicated_forest_paths()
        self.biome._check_active_forest_paths()
        # LATER: other health tests?

    @staticmethod
    def _check_dublicated_biome_files():
        # LATER: cls or self? how to handle multiple biomes?
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

            # MOVE: to biome,
            # - biome creates forest
            # - forest creates tree
            # - tree creates sprout
            # - data executes everything
            forest = Forest()
            forest.save_state(forest_file)
            data.biome.forests.append(forest_file)

        logger.info(f"New base created at:\n{base_dir}")

    def load_local_files_to_forest(self, clear_current_files=False):
        """Browse local files folder in camp and attach files to Forest"""

        # LATER: sort! by folder/section? check with shmoodle
        self.forest.load_local_files(
            from_empty_status=clear_current_files,
        )

    def load_prompt(
        self,
        prompt_path: Path | None = None,
        prompt_text: str | None = None,
        topic: str | None = None,
    ):
        """Load prompt in storage, Priority: text > path > read from file"""

        prompt: str = self._match_prompt_input_and_load(
            prompt_path, prompt_text
        )
        topic: str = (
            topic
            or self._extract_topic_from_prompt(prompt)
            or config.defaults.topic
        )
        logger.info(f"Prompt loaded with: {topic=}")

        self._prompt = Prompt(topic=topic, text=prompt)

    @staticmethod
    def _extract_topic_from_prompt(prompt: str) -> str:

        if lines := prompt.splitlines():
            first_non_empty_line: str | None = next(
                (line.strip() for line in lines if line.strip()), None
            )
            if first_non_empty_line:
                topic: str = slugify(first_non_empty_line, delim="-")
                return topic

        logger.error("Prompt is empty, fix that before model release!")
        raise AttributeError("Empty Prompt!")

    @staticmethod
    def _match_prompt_input_and_load(
        prompt_path: Path | None = None, prompt_text: str | None = None
    ) -> str:
        match (prompt_path, prompt_text):
            case (None, None):
                path: Path = Path.cwd() / config.names.prompt
                logger.info(f"Loading prompt from default path: {path}")
                prompt: str = path.read_text()

            case (Path() as path, None):
                logger.info(f"Loading prompt from custom path: {path}")
                prompt: str = path.read_text()

            case (None, str() as text):
                logger.info("Using prompt text from string input")
                prompt: str = text

            case (_, _):
                logger.error(f"Input sources:\n{prompt_path=}\n{prompt_text=}")
                raise AttributeError("Can't load prompt from 2 sources!")

        if not prompt:
            logger.error("Prompt is empty, fix that before model release!")
            raise AttributeError("Empty Prompt!")

        return prompt

    def attach(
        self, model: ModelFamily, tree_id: int = 0, topic: str | None = None
    ) -> Sprout:

        # NEXT: function of forest?
        # - here just preparation and decisions
        tree: Tree = self._find_or_create_tree(model, tree_id, topic)
        sprout: Sprout = tree.attach_fresh_sprout(self._prompt)

        return sprout

    def _find_or_create_tree(
        self, model: ModelFamily, tree_id: int, topic: str | None = None
    ) -> Tree:
        # MOVE: to forest?
        if not self.in_forest:
            raise FileNotFoundError("Not in Forest!")

        if tree_id == 0:
            tree_stem: str = topic or self._prompt.topic
            return self.forest.new_tree(
                model=model.unique, tree_stem=tree_stem
            )

        for existing_tree in self.forest.trees:
            if existing_tree.id == tree_id:
                if existing_tree.model != model.unique:
                    raise ValueError(
                        f"Invalid id! {model.unique=} must match: {existing_tree=} "
                    )
                return existing_tree
        else:
            raise ValueError(f"{tree_id=} < 0, use 0 for new tree")

    def load_files(self, files: list[Path], ensure_file_loaded=False):

        n_input_files: int = len(files)

        files_in_forest: list[UploadFile] = self.forest.load_files_from_path(
            [file for file in files if file.exists()]
        )

        n_confirmed_files: int = len(files_in_forest)

        if n_confirmed_files != n_input_files:
            logger.warning(f"{n_confirmed_files=} but {n_input_files=}!")
            if ensure_file_loaded:
                raise FileNotFoundError("Not all files confirmed!")
        else:
            logger.info(f"Attached all {n_input_files=} to data")

        self._files: list[UploadFile] = files_in_forest

    def load_images(self, images: list[Path], ensure_image_loaded=False):
        n_input_images: int = len(images)

        confirmed_images: list[Path] = [
            image for image in images if image.exists()
        ]

        n_confirmed_images: int = len(confirmed_images)

        if n_confirmed_images != n_input_images:
            logger.warning(f"{n_confirmed_images=} but {n_input_images=}!")
            if ensure_image_loaded:
                raise FileNotFoundError("Not all images confirmed!")
        else:
            logger.info(f"Attached all {n_input_images=} to data")

        self._images: list[Path] = confirmed_images

    def load_role(self, role_path: Path | None = None):
        """Role text overrides paths if provided"""
        if role_path is None:
            self._role_path: Path | None = None
            self._role: str | None = None
        else:
            self._role_path: Path | None = None
            self._role: str | None = role_path.read_text()
