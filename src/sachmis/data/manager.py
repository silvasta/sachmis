from pathlib import Path
from typing import Self

from loguru import logger
from sstcore.data import SstFile

from sachmis.data.conversation import Response

from ..config import SachmisConfig, get_config
from ..exceptions import ArborealError, DataRuntimeError, SachmisDataError
from .arboreal import ArborealTracker, Biome, Tree
from .camp import CampManager
from .files import Role, UploadFile
from .handler import DataHandler, FrontFileHandler
from .uploader import Uploader

config: SachmisConfig = get_config()


class DataManager:
    """Global orchestrator for medium-level Data tasks"""

    # LATER: prepare for multiple Trees
    _handler: DataHandler | None = None

    _front: FrontFileHandler | None = None
    _camp: CampManager | None = None
    _uploader: Uploader | None = None

    def __init__(self):
        """Setup and check required: Biome, Forest"""

        # TASK: check and compare: what if Forest has other Biome?

        # TODO: better intro text
        self.biome_file: Path = config.paths.biome_file()
        logger.info(f"Biome: {self.biome_file}")

    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
    ### ContextManager stuff
    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --

    def __enter__(self) -> Self:
        logger.info("DataManager: Loading Data in Context")
        self._full_responses: list[SstFile] = []
        self._front = FrontFileHandler()

        return self

    def __exit__(self, exception_type, exception_value, _exception_trace_back):
        logger.info("DataManager: Close data from context")

        if exception_type is not None:
            logger.error(f"DataManager - Error: {exception_type.__name__}")

            if issubclass(exception_type, ArborealError):
                # IMPORTANT: check if handle arbos separate, and what else
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
    def handler(self) -> DataHandler:  # LATER: prepare for multiple Trees
        if self._handler is None:
            raise DataRuntimeError("DataHandler not loaded!")
        return self._handler

    def attach_handler(self, tracker: ArborealTracker[Tree]):
        self._handler = DataHandler(tracker)
        logger.info(f"Attached: {self.handler.__class__.__name__}")

    @property
    def front(self) -> FrontFileHandler:  # LATER: prepare for multiple Setups
        if self._front is None:
            raise DataRuntimeError("DataHandler not loaded!")
        return self._front

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

    def extract_from_tree(self, tree):
        self.handler.extract_data_from_tree(
            tree,
            prompt_text=self.front._prompt_text,
            topic=self.front.topic,
        )

    def load_files(self, files: list[UploadFile]):
        uploaded: list[UploadFile] = self.uploader.load_files(files)
        self.handler.prompt.attach_files(uploaded)

    def load_role(self, path: Path | None):
        role: Role | None = self.camp.load_role(path)
        self.handler.prompt.attach_role(role)

    def handle_response(self, response: Response):
        self.handler.handle_response(response)
        self.front.handle_response(response)
        logger.success("handled Response")

    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
    ### Biome Level Tasks - remaining tasks
    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --

    def _add_temporary_full_response(self, text: str, path: Path) -> None:
        path.write_text(text)
        response: SstFile = SstFile(local_path=Path(path.name))
        self._full_responses.append(response)

    def _attach_new_full_responses_to_biome(self):

        with Biome.edit_mode(config.paths.biome_file()) as biome:
            biome.responses.extend(self._full_responses)

        logger.info(f"Attached {len(self._full_responses)} files to Biome")
        self._full_responses.clear()
