from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from loguru import logger
from sstcore import System
from sstcore.system import EmitFunctor
from sstcore.utils import Printer
from sstcore.utils.color import ColorBox

from sachmis.utils.events import DataEvent

from ...config import SachmisConfig
from ...utils.views import RichAmpel, SimpleNameMixin, Status, UploadViews
from ..files.upload import RemoteState, UploadFile, UploadState

TUploadState = TypeVar("TUploadState", bound=UploadState)

c: ColorBox = ColorBox()


class _View(UploadViews, SimpleNameMixin, RichAmpel):
    pass


class FileUploader(_View, ABC):
    """Public functions for upload and template for remotes"""

    @property
    @abstractmethod
    def target(self) -> str:
        """Name of Remote Provider"""  # LATER: use Provider Enum

    @property
    def printer(self) -> Printer:
        return self._system.printer

    @property
    def _config(self) -> SachmisConfig:
        return self._system.config

    def __init__(self, system: System, local_dir: Path | None = None):
        self._system: System = system
        self._emit: EmitFunctor = self._system.emitter.make(
            event_name=DataEvent.UPLOADER, sender=f"{self}"
        )
        self.online_files: list[UploadFile] = []
        self.local_dir: Path = local_dir or self._config.paths.file_dir
        self._load_client()
        logger.debug(f"Client Loaded: {self} ready!")

    @abstractmethod
    def _load_client(self) -> bool:
        """Connect to Remote with API key"""

    def get_online_files(self, refresh_registry=False) -> list[Any]:
        """Ensure online_files are fetched from remote registry"""
        if refresh_registry or self.online_files is None:
            self.online_files: list[Any] = self._fetch_all_files()
            self.status: Status = Status.FETCHED
        return self.online_files

    @abstractmethod
    def _fetch_all_files(self) -> list[Any]:
        """Load all available files from remote registry"""

    def get_remote_states(self, refresh_registry=False) -> list[RemoteState]:
        """Transform all fetched Online Files to project RemoteStates"""
        return [  # LATER: maybe cache somehow, but refreshable
            self._to_remote_state(online_file)
            # WARN: maybe errors?
            for online_file in self.get_online_files(refresh_registry)
        ]

    @abstractmethod
    # IDEA: make this classmethod on RemoteStates?
    # - again same issue with class attach to Uploader...
    def _to_remote_state(self, online_file: Any) -> RemoteState:
        """Transform raw Online File to Sachmis Remote State with identifier"""

    def sync_local_file(self, file: UploadFile, ensure_after_upload=False):
        """Check and ensure that file is uploaded"""

        local_ok: bool = file.confirm_local_status(self.local_dir)
        remote_ok: bool = self.confirm_remote_status(file)

        match (local_ok, remote_ok):
            case (True, True):
                logger.debug(f"File is online: {file.name}")
                # TODO: emit, use File? with Status?
            case (True, False):
                logger.debug(f"File ready for upload: {file.name}")
                self.upload_file(file)
            case (False, True):
                logger.warning("File Online but Missing Local!")
            case (False, False):
                logger.error(
                    f"File Missing Online and Local: {self.local_dir}"
                )  # LATER: better Error
                raise FileNotFoundError(f"{file.local_path=}")

        if ensure_after_upload:
            if self.confirm_remote_status(file):
                logger.debug(f"Confirmed after upload: {file.name}")
            else:
                raise RuntimeError(f"Check failed after upload: {file.name}")

    def confirm_remote_status(self, file: UploadFile) -> bool:
        """Check if RemoteState exists, is valid and in Online Registry"""
        if not (remote_state := file.find_remote(self.target)):
            return False
        remote_matches: list[RemoteState] = [
            online_state
            for online_state in self.get_remote_states()
            if online_state.remote_id == remote_state.remote_id
        ]
        if remote_state.is_valid() and len(remote_matches) == 1:
            return True
        if len(remote_matches) > 1:
            raise RuntimeError("Duplicated Remote Files!", remote_matches)
        logger.debug(f"Removing invalid RemoteState: {remote_state}")
        file.remove_remote(self.target)
        return False

    @abstractmethod
    def upload_file(self, file: UploadFile) -> UploadFile:
        """Upload 1 file and attach RemoteState to UploadFile"""
        state: RemoteState = self._upload(file)
        file.attach_remote(state)
        self._emit(**{"uploaded": file})
        return file

    @abstractmethod
    def _upload(self, file: UploadFile) -> RemoteState:
        """Copy Local File to Remote Registry and collect State"""

    def show_all_files(self, refresh=False):
        """Show all available files on remote"""

        self.printer.title(f"{self}: Fetching files...")

        online_states: list[RemoteState] = self.get_remote_states(refresh)
        header = f"{c.cyan(self)}Files: {len(online_states)}"
        title: str = self.__rich__()
        self.printer.title(header, title)
        self.printer(online_states)

    @abstractmethod
    def _remove(self, online_file: Any) -> bool:
        """Remove remote file and confirm success"""

    def delete_all_uploaded_files(self):
        """Clear remote, may break stored messages for further usage!"""

        online_files: list[Any] = self._fetch_all_files()
        logger.info("Start deleting files")
        n_deleted = 0

        for online_file in online_files:
            n_deleted += 1 if self._remove(online_file) else 0

        if (n_files := len(online_files)) == n_deleted:
            self.printer.success(f"Deleted all {n_deleted} of {n_files} files")
        else:
            self.printer.danger(f"{n_deleted=} but {n_files=}")

    def compare_with_online_files(
        self, local_files: list[UploadFile]
    ) -> CompareResult:

        # AI_TASK: repair this, clean up, structure:
        # - most of the work done be CompareResult, RemoteState and UploadFile
        # __dunder__ for log, and print
        local_identifier: set[str] = self._get_local_identifier(local_files)
        remote_identifier: set[str] = self._get_remote_identifier()

        logger.debug(f"{local_identifier=}")
        logger.debug(f"{remote_identifier=}")

        intersection_identifier: set[str] = (
            local_identifier & remote_identifier
        )
        only_local_identifier: set[str] = local_identifier - remote_identifier
        only_local_no_identifier: list[UploadFile] = [
            file for file in local_files if not file.has_remote(self.target)
        ]
        only_remote_identifier: set[str] = remote_identifier - local_identifier

        logger.debug(f"{intersection_identifier=}")
        logger.debug(f"{only_local_identifier=}")
        logger.debug(f"{only_local_no_identifier=}")
        logger.debug(f"{only_remote_identifier=}")

        _all = [
            intersection_identifier,
            only_local_identifier,
            only_local_no_identifier,
            only_remote_identifier,
        ]
        # IDEA: function of CompareResult
        n_files: int = sum(map(len, _all))

        intersection: list[UploadFile] = self._get_local_file_from_identifier(
            local_files, identifier=intersection_identifier
        )
        only_local: list[UploadFile] = (
            self._get_local_file_from_identifier(
                local_files, identifier=only_local_identifier
            )
            + only_local_no_identifier
        )
        only_remote: list[str] = self._get_remote_file_from_identifier(
            identifier=only_remote_identifier
        )

        result = CompareResult(
            intersection_identifier=intersection_identifier,
            only_local_identifier=only_local_identifier,
            only_remote_identifier=only_remote_identifier,
            intersection=intersection,
            only_local=only_local,
            only_remote=only_remote,
        )

        printer.special(f"Statistics for {self.__class__.__name__}")

        # IDEA: function of CompareResult
        frac = f"{len(only_local)}/{n_files}"
        printer.lines(
            lines=[file.description for file in only_local],
            header=f"Files only in Local registry {frac}",
            title=f"Local - {self.print_name}",
            style="blue",
        )

        frac = f"{len(intersection)}/{n_files}"
        printer.lines(
            lines=[file.description for file in intersection],
            header=f"Intersection of Local and Remote Files {frac}",
            title=f"Intersection - {self.print_name}",
            style="green",
        )

        frac = f"{len(only_remote)}/{n_files}"
        printer.lines(
            lines=only_remote,
            header=f"Files only in Remote registry {frac}",
            title=f"Global - {self.print_name}",
            style="orange3",
        )
        return result

    def _delete_not_in_list(self, local_files: list):
        # IMPORTANT: this one was one of the most useful ones,
        # - deleting duplicated uploads while dont breaking contexts with delete too much
        # AI_TASK: ensure this works stable again
        online_files: Any = self.client.files.list()
        local_ids = set(
            file.x_id for file in local_files if file.x_id is not None
        )
        for online_file in online_files.data:
            if online_file.id in local_ids:
                logger.success(f"file confirmed: {online_file.filename}")
            else:
                # self.delete_one_file(online_file)
                pass


@dataclass
class CompareResult:
    """Data container for files split by local or remote status"""

    intersection_identifier: set[str]
    only_local_identifier: set[str]
    only_remote_identifier: set[str]

    intersection: list[UploadFile]
    only_local: list[UploadFile]
    only_remote: list[str]
