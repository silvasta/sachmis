from pathlib import Path
from typing import Self

from loguru import logger
from sstcore.data import SstFile

from ..config import SachmisConfig, get_config
from ..exceptions import ArborealError, DataRuntimeError, SachmisDataError
from .arboreal import Biome
from .camp import CampManager
from .files import Role, UploadFile
from .handler import DataHandler
from .uploader import Uploader

config: SachmisConfig = get_config()


class DataManager:
    """Global orchestrator for medium-level Data tasks"""

    _handler: DataHandler | None = None
    _camp: CampManager | None = None
    _uploader: Uploader | None = None

    def __init__(self, handler: DataHandler):
        """Setup and check required: Biome, Forest"""

        # TASK: check and compare Biome/Forest,
        # what if Forest has other Biome?

        # TODO: better intro text
        self.biome_file: Path = config.paths.biome_file()
        logger.info(f"Biome: {self.biome_file}")
        self._full_responses: list[SstFile] = []

        self.attach_handler(handler)

    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
    ### ContexManager stuff
    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --

    def __enter__(self) -> Self:
        logger.info("DataManager: Loading Data in Context")
        return self

    def __exit__(self, exception_type, exception_value, _exception_trace_back):
        logger.info("DataManager: Close data from context")

        if exception_type is not None:
            logger.error(f"DataManager - Error: {exception_type.__name__}")

            if issubclass(exception_type, ArborealError):
                # IMPORTANT: check if handle arbos sepatat, and what else
                logger.error(f"Context: {exception_value=}")
                logger.warning("State not saved!")
                return config.defaults.context.data_error_arboreal.swallow

            if issubclass(exception_type, SachmisDataError):
                # IMPORTANT: handle all Data issues here
                logger.error(f"SachmisDataError: {exception_value}")
                logger.warning("State not saved!")
                return config.defaults.context.data_error_sachmis.swallow

            logger.warning("State not saved!")

        if self._full_responses:
            self._attach_new_full_responses_to_biome()

        logger.info("DataManager: Clean Exit")

        return config.defaults.context.data_end.swallow

    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
    ### Handlers
    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --

    @property
    def handler(self) -> DataHandler:
        if self._handler is None:
            raise DataRuntimeError("DataHandler not loaded!")
        return self._handler

    def attach_handler(self, handler: DataHandler):
        self._handler: DataHandler = handler
        logger.info(f"Attached: {handler.__class__.__name__}")

    @property
    def camp(self) -> CampManager:
        if self._camp is None:
            raise DataRuntimeError("Camp not loaded!")
        return self._camp

    def attach_camp(self, camp: CampManager):
        self._camp: CampManager = camp
        logger.info(f"Attached: {camp.__class__.__name__}")

    @property
    def uploader(self) -> Uploader:
        if self._uploader is None:
            self._uploader = Uploader()
        return self._uploader

    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
    ### Handler Communication
    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --

    def load_files(self, files: list[UploadFile]):
        uploaded: list[UploadFile] = self.uploader.load_files(files)
        self.handler.prompt.attach_files(uploaded)

    def load_role(self, path: Path | None):
        role: Role | None = self.camp.load_role(path)
        self.handler.prompt.attach_role(role)

    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
    ### Biome Level Tasks - remaining tasks
    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --

    def _add_temporary_full_response(self, text: str) -> None:
        # NEXT:
        path.write_text(text)
        response: SstFile = SstFile(local_path=Path(path.name))
        self._full_responses.append(response)

    def _attach_new_full_responses_to_biome(self):

        with Biome.edit_mode(config.paths.biome_file()) as biome:
            biome.responses.extend(self._full_responses)

        logger.info(f"Attached {len(self._full_responses)} files to Biome")
        self._full_responses.clear()
