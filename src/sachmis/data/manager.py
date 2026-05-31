from itertools import product
from pathlib import Path
from typing import Literal, Self

from loguru import logger
from rich.prompt import Confirm
from sstcore.data import SstFile

from ..config import SachmisConfig, get_config
from ..exceptions import (
    ArborealError,
    ArborealFileMissingError,
    DataRuntimeError,
    SachmisError,
)
from ..utils import printer
from .arboreal import Biome
from .conversation import ResponseData
from .files import CampManager, UploadFile
from .handler import FileHandler
from .uploader import RemoteUploader, create_uploader

config: SachmisConfig = get_config()


class DataManager:
    """Loads Pydantic models on entry, saves them on clean exit."""

    _handler: FileHandler | None = None
    _camp: CampManager | None = None
    _uploader: dict[str, RemoteUploader] = {}

    @property
    def has_handler(self) -> bool:
        return self._handler is not None

    @property
    def handler(self) -> FileHandler:
        if self._handler is None:
            raise DataRuntimeError("FileHandler not loaded!")
        return self._handler

    @property
    def camp(self) -> CampManager:
        if self._camp is None:
            raise DataRuntimeError("Camp not loaded!")
        return self._camp

    def get_uploader(self, target: str) -> RemoteUploader:
        if target not in self._uploader:
            self._uploader[target] = create_uploader(target)
        return self._uploader[target]

    def __init__(self, biome=False, forest=False):
        """Setup and check required: Biome, Forest"""

        self._needs_biome: bool = biome
        self._needs_forest: bool = forest

        if self._needs_biome:
            try:
                self.biome_file: Path = config.paths.biome_file
                logger.debug(f"biome: {self.biome_file}")
            except FileNotFoundError:
                # REFACTOR: out of data.manager or at least __init__
                printer.warn("Biome File Missing")
                Literal["create", "raise", "prompt"]
                text = "Create New Biome from default names?"
                strategy: str = config.defaults.cli.data_no_biome
                if strategy == "create" or (
                    strategy == "prompt"
                    and Confirm.ask(prompt=text, default=True)
                ):
                    Biome.with_name()
                    printer.success("DataManager Setup recovered!")
                else:
                    raise ArborealFileMissingError(
                        "Biome", config.paths._biome_file()
                    ) from None

            self._full_responses: list[SstFile] = []

        if self._needs_forest:
            self.forest_file: Path = config.paths.forest_file
            logger.debug(f"forest: {self.forest_file}")

    def __enter__(self) -> Self:
        logger.info("DataManager: Load data in Context")
        return self

    def __exit__(self, exception_type, exception_value, _exception_trace_back):
        logger.info("DataManager: Close data from context")

        if exception_type is not None:
            logger.error(f"DataManager - Error: {exception_type.__name__}")

            if issubclass(exception_type, ArborealError):
                logger.error(f"Context: {exception_value=}")
                logger.warning("State not saved!")
                return config.defaults.context.data_error_arboreal.swallow

            if issubclass(exception_type, SachmisError):
                logger.error(f"SachmisError: {exception_value}")
                logger.warning("State not saved!")
                return config.defaults.context.data_error_sachmis.swallow

            logger.warning("State not saved!")

        if self._needs_biome and self._full_responses:
            self._attach_new_full_responses_to_biome()

        logger.info("DataManager: Clean Exit")

        return config.defaults.context.data_end.swallow

    def _attach_new_full_responses_to_biome(self):
        if not self._needs_biome:
            raise ArborealError("Invalid call for data with biome=False")

        with Biome.edit_mode(config.paths.biome_file) as biome:
            biome.responses.extend(self._full_responses)

        logger.info(f"Attached {len(self._full_responses)} files to Biome")
        self._full_responses.clear()

    def _add_temporary_full_response(self, text: str, path: Path) -> None:

        # TASK: handle path creation here?

        path.write_text(text)
        response: SstFile = SstFile(local_path=Path(path.name))

        self._full_responses.append(response)

    def attach_handler(self, handler: FileHandler):
        self._handler: FileHandler = handler
        logger.info(f"Attached: {handler.__class__.__name__}")

    def attach_camp(self, camp: CampManager):
        self._camp: CampManager = camp

    # MOVE: camp
    def load_files(self, files: list[UploadFile], ensure_after_upload=True):
        """Assumes valid local data files, pushes to Remotes"""

        # TODO: files

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

    # MOVE: camp
    def load_images(self, images: list[SstFile]):
        """Assumes valid local image files, pushes to Remotes"""

        # TODO: images

        logger.debug("attaching files to data.image")
        prompt_files: list[SstFile] = self.prompt.images
        prompt_files.extend(images)

    def load_role(self, role_path: Path | None = None):
        # MOVE: together with role stuff
        if role_path is not None and (role := role_path.read_text()):
            self._role_path: Path | None = role_path
            self._role: str | None = role

    ### --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    ### --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

    ### --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    ### --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

    def handle_response(self, response: ResponseData):
        """So far: write when desired, later handle filetree | other.."""
        # IMPORTANT: check load Tree! save intermediate?

        # MOVE: handler
        if not self._prompt_written:
            self._result_file_paths.append(self._rotate_prompt())
            self._prompt_written = True

        # TODO: attach response to prompt

        answer_path: Path = response.write()
        self._result_file_paths.append(answer_path)

        logger.info(f"Response written to: {answer_path=}")
