from pathlib import Path
from typing import Self

from loguru import logger
from sstcore.data import SstFile
from sstcore.utils.print import ColorBox

from ..config import SachmisConfig, get_config
from ..exceptions import ArborealError, DataRuntimeError, SachmisDataError
from ..utils import printer
from .arboreal import ArborealTracker, Biome, Tree
from .camp import CampManager
from .conversation import Response
from .files import Role, UploadFile
from .handler import DataHandler, FrontFileHandler
from .uploader import Uploader

config: SachmisConfig = get_config()


class DataManager:
    """Global orchestrator for medium-level Data tasks"""

    # TASK: check and compare: what if Forest has other Biome than before?

    _handler: DataHandler | None = None  # LATER: prepare for multiple Trees

    _front: FrontFileHandler | None = None
    _camp: CampManager | None = None
    _uploader: Uploader | None = None

    def __init__(self):
        """Setup and check required: Biome, Forest"""
        self.biome_file: Path = config.paths.biome_file()
        logger.info(f"Biome: {self.biome_file}")
        printer(self)

    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
    ### START of Representation
    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --

    def __repr__(self):
        manager: str = type(self).__name__
        return (  # LATER: check for loop over handlers, check {_handler!r}
            f"{manager}("
            f"_handler={self._handler}, "
            f"_front={self._front}, "
            f"_camp={self._camp}, "
            f"_uploader={self._uploader}"
            f")"
        )

    def _all_not_none_handler(self) -> list[str]:
        handlers: list = [
            self._handler,
            self._front,
            self._camp,
            self._uploader,
        ]
        return [type(h).__name__ for h in handlers if h is not None]

    def __str__(self) -> str:
        return self._assemble_str(self._all_not_none_handler())

    def _assemble_str(self, all_handler: list[str] | None = None, manager=""):
        """Dispatch for __str__ and colorful: defaults for __str__"""
        _manager: str = manager or type(self).__name__
        _all_not_none_handler: list[str] = (
            all_handler
            if all_handler is not None
            else self._all_not_none_handler()
        )
        return f"{_manager}[{', '.join(_all_not_none_handler)}]"

    @property
    def colorful(self) -> str:
        c: ColorBox = ColorBox.with_mode("bold")
        manager: str = c(type(self).__name__, color="royal_blue1")
        handler: list[str] = [
            c(handler, color="steel_blue1")
            for handler in self._all_not_none_handler()
        ]
        return c(self._assemble_str(handler, manager), color="white")

    @property
    def _cli(self) -> str:
        return self.colorful

    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
    ### END of Representation
    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --

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
        c: ColorBox = ColorBox.with_mode("bold")

        if exception_type is not None:
            error = exception_type.__name__
            logger.error(f"DataManager - {error}: {exception_value}")
            printer.header(
                f"{c.red(error)} {exception_value}",
                frame="red",
                subtitle=f"{self._cli}",
                subtitle_align="right",
            )

            input()

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
