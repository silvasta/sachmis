import sys
from pathlib import Path

from boltons.strutils import slugify
from loguru import logger
from silvasta.utils import PathGuard

from sachmis.config import SachmisConfig, get_config
from sachmis.config.model import ModelFamily
from sachmis.data.files import Prompt, UploadFile
from sachmis.data.uploader import FileUploader
from sachmis.data.uploader import get_upload_cls
from sachmis.utils.print import printer

from .arboreal import Biome, Forest, Sprout
from .uploader import RemoteUploader  # noqa: E402

config: SachmisConfig = get_config()


class DataManager:
    """Loads Pydantic models on entry, saves them on clean exit."""

    # MOVE:
    uploader: list[RemoteUploader] = []

    # TODO: single dispach by filetype?
    def get_uploader(self, target: str) -> RemoteUploader:
        # TEST: works with derived class?
        for u in self.uploader:
            if u.target == target:
                return u
        new_uploader: RemoteUploader = get_upload_cls(target)()
        self.uploader.append(new_uploader)
        return new_uploader

    def __init__(self, save_at_exit=True, forest_required=False):

        self.save_at_exit: bool = save_at_exit
        # LATER: this to __init__(...)?
        self._write_to_cwd: bool = False
        self._answer_file_paths: list[Path] = []

        if config.paths.biome_file.exists():
            logger.info("Biome file exists")
        else:
            logger.warning("Biome file not found, create new?")
            # TODO: create biome here? wait for task!
            # - or raise here?

        if config.paths.in_base:
            logger.debug("Current location in base")

            if config.paths.forest_file.exists():
                logger.debug("Forest file exists")
            else:
                logger.warning(f"Not found:{config.paths.forest_file=}")
            self.in_forest = True
        else:
            self.in_forest = False

        logger.info(f"DataManager: {self.in_forest=}")

        if forest_required and not self.in_forest:
            # LATER: personalized exception, NotInForestError?
            raise FileNotFoundError("Not in Forest!")

    def __enter__(self) -> "DataManager":
        logger.info("DataManager: Load data in Context")

        try:
            self.biome: Biome = Biome.load_state()
            # TASK: hande missing biome
            # - check if biome_required in init make sense
            # - check in self._with_biome makes sense
            # - check for personalized exception
            # so far: check in init, check in load raise exception, catch exception here...
        except AttributeError as e:
            logger.error(f"Problem with loading biome! {e}")
            sys.exit(1)

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

            if issubclass(exception_type, AttributeError):
                # TEST: used for biome not found, where else?
                # - personalized Exceptions! coming soon...
                logger.error(f"Context: {exception_value=}")
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

    @property
    def most_recent_topic(self) -> str:
        """Get the topic of the last loaded prompt or '' (empty string)"""
        return self._prompt.topic if hasattr(self, "_prompt") else ""

    @property
    def answer_file_path_strings(self) -> list[str]:
        """Get the current state of the answer file paths formated as string"""
        return [str(answer) for answer in self._answer_file_paths]

    def check_health_biome(self):
        DataManager._check_dublicated_biome_files()
        self.biome._prune_dublicated_forest_paths()
        self.biome._check_active_forest_paths()
        # LATER: other health tests?
        logger.debug("biome healthcheck completed")

    @staticmethod
    def _check_dublicated_biome_files():
        # LATER: cls or self? how to handle multiple biomes?
        biome_files: list[Path] = PathGuard.find_sequence(
            config.paths.biome_file
        )
        if num_biome_files := len(biome_files) > 1:
            logger.warning(f"For current biome path: {num_biome_files=}")
            for file in biome_files:
                printer(file)
            logger.debug(f"current status: {biome_files=}")

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
            # MOVE: somehow into PathGuard?
            if base_dir_unconfirmed != base_dir:
                printer.danger(f"Detected Folder with new {base_name=}!")
                logger.warning(f"Using: {base_dir_unique=}")

            promp_path: Path = base_dir / config.names.prompt
            PathGuard.file(promp_path, default_content="", raise_error=False)

            camp_name: str = config.names.camp_dir
            camp_dir: Path = PathGuard.dir(base_dir / camp_name)

            # LATER: local structure in camp
            # - config file(s)?
            # - roles?
            # - etc..

            printer.success("Files and dirs ready: creating Forest now!")

            forest_file: Path = camp_dir / config.names.forest_file
            data.biome.attach_new_forest(forest_file)

        logger.info(f"New base created at:\n{base_dir}")

    def load_local_files_to_forest(
        self,
        clear_current_files=False,
        local_file_dir: Path | None = None,
    ):
        """Browse local files folder (default .camp/files) and attach files to Forest"""

        self.forest.load_local_files(
            local_file_dir=local_file_dir,
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

        self._prompt = Prompt(topic=topic, text=prompt)
        logger.info(f"Prompt loaded with: {topic=}")

        # Wait for first response, in case something fails
        self._prompt_written = False

    def _move_or_write_prompt(self):
        new_prompt_path: Path = config.paths.prompt_file(self._prompt.topic)

        if self._input_prompt_path is None:
            new_prompt_path.write_text(self._prompt.text)
        else:
            PathGuard.rotate(
                source=self._input_prompt_path,
                target=new_prompt_path,
                reset=True,
            )
        self._answer_file_paths.append(new_prompt_path)

    def handle_response(self, sprout: Sprout):
        """So far: write when desired, later handle filetree | other.."""
        if not self._write_to_cwd:
            logger.debug("No response handling")
            return
        if not self._prompt_written:
            self._move_or_write_prompt()
            self._prompt_written = True
            logger.debug(f"{self._prompt_written}")

        if sprout.response is None:
            logger.error(f"Can't process empty response of {sprout=}")
        else:
            answer_path: Path = sprout.write_answer_get_path
            self._answer_file_paths.append(answer_path)
            logger.debug(f"written to: {answer_path=}")

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

    def _match_prompt_input_and_load(
        self, prompt_path: Path | None = None, prompt_text: str | None = None
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
                path = None

            case (_, _):
                logger.error(f"Input sources:\n{prompt_path=}\n{prompt_text=}")
                raise AttributeError("Can't load prompt from 2 sources!")

        if not prompt:
            logger.error("Prompt is empty, fix that before model release!")
            raise AttributeError("Empty Prompt!")

        self._input_prompt_path: Path | None = path
        return prompt

    def attach(self, model: ModelFamily, tree_locator: str = "") -> Sprout:

        if not self.in_forest:
            raise FileNotFoundError("Not in Forest!")

        if tree_locator:
            # TODO: maybe check from here if tree valid and handle error
            logger.debug(f"{tree_locator=}")
            sprout: Sprout = self.forest.attach_sprout_in_tree(
                tree_locator=tree_locator,
                model=model.unique,
                prompt=self._prompt,
            )
        else:
            sprout: Sprout = self.forest.attach_new_tree(
                model=model.unique, prompt=self._prompt
            ).sprout

        return sprout  # NOTE: save forest here? (or somewhen before release?)

    def find_previous_id(self, tree_locator) -> str:
        sprout: Sprout = self.forest.find_sprout_in_tree(tree_locator)
        logger.debug("found sprout")
        if sprout.response:
            return sprout.response.id
        raise ValueError(f"no response for {tree_locator=}")

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
            logger.info(f"Attach all {n_input_files=} to data")

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
            logger.info(f"Attach all {n_input_images=} to data")

        self._images: list[Path] = confirmed_images

    def load_role(self, role_path: Path | None = None):
        """Role text overrides paths if provided"""  # NOTE: ??

        # TODO: create text input arg, input generates new role file

        if role_path is not None and (role := role_path.read_text()):
            self._role_path: Path = role_path
            self._role: str = role
            logger.warning("role")
        else:
            self._role_path: Path | None = None
            self._role: str | None = None
            logger.warning("no role")

    # TASK: file roleout
    # - so far flat in 1 folder
    # - group by tree?
