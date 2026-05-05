from itertools import product
from pathlib import Path
from typing import Self

from loguru import logger
from sstcore import PathGuard
from sstcore.data import SstFile

from ..config import SachmisConfig, get_config
from ..exceptions import (
    ArborealError,
    ArborealFileExistsError,
    SachmisDataError,
    SachmisError,
)
from ..exceptions.data import DataManagerRuntimeError
from .arboreal import ArborealTracker, Biome, Forest, Sprout, Tree
from .files import CampManager, UploadFile
from .prompt import Prompt
from .uploader import RemoteUploader, create_uploader


class DataManager:
    """Loads Pydantic models on entry, saves them on clean exit."""

    _camp: CampManager | None = None
    _prompt: Prompt | None = None
    _uploader: dict[str, RemoteUploader] = {}

    _extracted_sprouts: dict[str, ArborealTracker] = {}
    _answer_file_paths: list[Path] = []

    # MOVE: to sprout: role as something like Role(SstFile)
    _role_path: Path | None = None
    _role: str | None = None

    @property
    def role_name(self) -> str:  # MOVE: together with role stuff
        return self._role_path.name if self._role_path else "role from text"

    @property
    def camp(self) -> CampManager:
        if self._camp is None:
            raise DataManagerRuntimeError
        return self._camp

    @property
    def prompt(self) -> Prompt:
        if self._prompt is None:
            raise DataManagerRuntimeError("No prompt loaded...")
        return self._prompt

    @property
    def answer_file_paths(self) -> list[Path]:
        """Get the current state of the answer file paths"""
        return self._answer_file_paths

    def get_uploader(self, target: str) -> RemoteUploader:
        if target not in self._uploader:
            self._uploader[target] = create_uploader(target)
        return self._uploader[target]

    def __init__(self, biome=False, forest=False, camp=False):
        """Define at init what is required: Biome, Forest, inside Camp"""
        config: SachmisConfig = get_config()

        self._needs_biome: bool = biome
        self._needs_forest: bool = forest
        self._needs_inside_camp: bool = camp

        if self._needs_biome:
            try:
                self.biome_file: Path = config.paths.biome_file
                logger.debug(f"biome: {self.biome_file}")
            except FileNotFoundError:
                raise ArborealFileExistsError(
                    "Biome", config.paths._biome_file()
                ) from None
            self._full_responses: list[SstFile] = []

        if self._needs_forest:
            self.forest_file: Path = config.paths.forest_file
            logger.debug(f"forest: {self.forest_file}")

        if self._needs_inside_camp:
            self.camp_dir: Path = config.paths.camp_dir_as_parent
            logger.debug(f"camp: {self.camp_dir}")

    def __enter__(self) -> Self:
        logger.info("DataManager: Load data in Context")

        # TASK: Data start?

        return self

    def __exit__(self, exception_type, exception_value, _exception_trace_back):
        logger.info("DataManager: Close data from context")

        # TASK: Exception handling

        if exception_type is not None:
            logger.error(f"DataManager - Error: {exception_type.__name__}")

            if issubclass(exception_type, ArborealError):
                logger.error(f"Context: {exception_value=}")
                logger.warning("State not saved!")
                # Suppress exception (after handling it here)
                return True

            if issubclass(exception_type, SachmisError):
                logger.error(f"SachmisError: {exception_value}")
                logger.warning("State not saved!")
                # Suppress exception (after handling it here)
                return True

            logger.warning("State not saved!")

        if self._extracted_sprouts:
            logger.error("Not all Sprouts arrived well..")
            logger.error(f" No answer from: {self._extracted_sprouts=}")

        if self._needs_biome and self._full_responses:
            self._attach_new_full_responses_to_biome()

        # TASK: Data finish?

        logger.info("DataManager: Clean Exit")

        # Propagate exception to caller
        return False

    def track_extracted_sprout(
        self, sprout: Sprout, tree_tracker: ArborealTracker
    ):
        if not self._needs_forest:
            raise ArborealError("Invalid call for data with forest=False")
        if sprout.unique_id in self._extracted_sprouts:
            raise SachmisDataError("Sprout ID already in registry")

        self._extracted_sprouts[sprout.unique_id] = tree_tracker
        logger.debug(f"linked: {tree_tracker.path.name}, {sprout.unique_id=} ")

    def _attach_sprout_to_tree(self, sprout: Sprout):
        logger.debug("attaching final sprout back to tree")
        tracker: ArborealTracker = self._extracted_sprouts[sprout.unique_id]
        Tree.reattach_sprout(tree_file=tracker.path, sprout=sprout)

    def _attach_new_full_responses_to_biome(self):
        if not self._needs_biome:
            raise ArborealError("Invalid call for data with biome=False")

        config: SachmisConfig = get_config()

        with Biome.edit_mode(config.paths.biome_file) as biome:
            biome.responses.extend(self._full_responses)
            # LATER: clear _full_responses?

        logger.info(f"Attached {len(self._full_responses)} files to Biome")

    def _add_temporary_full_response(self, text: str, path: Path) -> None:

        path.write_text(text)
        response: SstFile = SstFile(local_path=Path(path.name))

        self._full_responses.append(response)

    def load_prompt(
        self, source: str | Path | None = None, topic: str | None = None
    ) -> Prompt:
        if isinstance(source, str):
            self._prompt: Prompt = Prompt.load_from_text(source, topic)
            self._input_prompt_path: Path | None = None
        else:
            config: SachmisConfig = get_config()
            path: Path = source or Path(config.names.prompt)
            self._prompt: Prompt = Prompt.load_from_path(path, topic)
            self._input_prompt_path: Path | None = path

        self._prompt_written = False

        return self._prompt

    def load_camp(self, forest: Forest):
        self._camp: CampManager = forest.provide_camp()

    def load_files(self, files: list[UploadFile], ensure_after_upload=True):
        """Assumes valid local data files, pushes to Remotes"""

        logger.debug("attaching files to data.prompt")

        prompt_files: list[UploadFile] = self.prompt.files

        for file, uploader in product(files, self._uploader.values()):
            try:
                uploader.upload_local_file(file, ensure_after_upload)
                prompt_files.append(file)
            except FileNotFoundError:
                logger.error(f"Missing {file=}")
            except RuntimeError as err:
                logger.error(f"Upload failed {file=}, {err}")
                # TODO: check if raise or not

    def load_images(self, images: list[SstFile]):
        """Assumes valid local image files, pushes to Remotes"""

        logger.debug("attaching files to data.image")

        prompt_files: list[SstFile] = self.prompt.images
        # TODO: any checks, logs, or prints?

        prompt_files.extend(images)

    def load_role(self, role_path: Path | None = None):
        if role_path is not None and (role := role_path.read_text()):
            self._role_path: Path | None = role_path
            self._role: str | None = role

    ### --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    ### --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

    ### --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    ### --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

    def _move_or_write_prompt(self):

        # TASK: file rollout
        new_prompt_path: Path = self.prompt.get_path(root_dir=Path.cwd())

        if self._input_prompt_path is None:
            new_prompt_path.write_text(self.prompt.text)
        else:
            PathGuard.rotate(
                source=self._input_prompt_path,
                target=new_prompt_path,
                reset=True,
            )
        self._answer_file_paths.append(new_prompt_path)
        logger.debug(f"prompt moved: {new_prompt_path=}")

    def handle_response(self, sprout: Sprout):
        """So far: write when desired, later handle filetree | other.."""

        if sprout.response is None:
            logger.error(f"Can't process empty response of {sprout=}")
            return

        # TASK: file rollout

        if not self._prompt_written:
            self._move_or_write_prompt()
            self._prompt_written = True

        answer_path: Path = sprout.answer_path_and_write(root_dir=Path.cwd())
        logger.info("answer")
        self._answer_file_paths.append(answer_path)

        logger.debug(f"written to: {answer_path=}")
