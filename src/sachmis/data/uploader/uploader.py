from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from loguru import logger

from sachmis.config import SachmisConfig, get_config
from sachmis.data.files import (
    RemoteState,
    UploadFile,
    UploadState,
)
from sachmis.utils.print import printer

TUploadState = TypeVar("TUploadState", bound=UploadState)

config: SachmisConfig = get_config()


@dataclass
class CompareResult:
    """Data container for files splitted by local or remote status"""

    intersection_identifier: set[str]
    only_local_identifier: set[str]
    only_remote_identifier: set[str]

    intersection: list[UploadFile]
    only_local: list[UploadFile]
    only_remote: list[str]


class FileUploader(ABC):
    """Public functions for upload and template for remotes"""

    client: Any
    remote_files = None

    @property
    @abstractmethod
    def target(self) -> str:
        """Name of remote as defined in UploadFile"""

    @property
    @abstractmethod
    def print_name(self) -> str:
        """Name of remote styled for print"""

    @property
    @abstractmethod
    def remote_state_cls(self) -> TUploadState:
        """Derived class of UploadState"""

    def __init__(self, local_dir: Path | None = None):
        self.local_dir: Path = local_dir or config.paths.file_dir
        self._load_client()
        logger.debug(f"{self.__class__.__name__} ready")

    @abstractmethod
    def _load_client(self) -> bool:
        """Connect to Remote with API key"""

    def refresh_remote_registry(self):
        self.get_remote_files(refresh_registry=True)

    def get_remote_files(self, refresh_registry=False) -> Any:
        """Ensure remote_files are loaded in remote registry"""
        if refresh_registry or self.remote_files is None:
            self.remote_files: list[Any] = self._fetch_all_files()

        return self.remote_files

    @abstractmethod
    def _fetch_all_files(self) -> list[Any]:
        """Load all avaliable files from remote registry"""

    def upload_local_file(self, file: UploadFile, ensure_after_upload=False):
        """Check and ensure that file is uploaded"""

        local_ok: bool = file.confirm_local_status(self.local_dir)
        remote_ok: bool = self.confirm_remote_status(file)

        match (local_ok, remote_ok):
            case (True, True):
                logger.debug(f"File is online: {file.name}")
            case (True, False):
                logger.debug(f"File ready for upload: {file.name}")
                state: RemoteState = self._upload_local_file(file)
                file.attach_remote(state)
            case (False, True):
                logger.warning("File is online but missing local!")
            case (False, False):
                local_dir = self.local_dir
                logger.error(f"File not online and missing in {local_dir=}!")
                raise FileNotFoundError(f"{file.local_path=}")

        if ensure_after_upload:
            if self.confirm_remote_status(file):
                logger.debug(f"Confirmed after upload: {file.name}")
            else:
                raise RuntimeError(f"Check failed after upload: {file.name}")

    def confirm_remote_status(self, file: UploadFile) -> bool:
        """Check if 'file' is valid in cached remote file list"""

        if not file.has_remote(self.target):
            return False
        logger.debug(file.has_remote(self.target))

        self.refresh_remote_registry()  # Important for _confirm_online

        if not (remote_is_valid := self._confirm_online(file)):
            invalid_state: RemoteState | None = file.remove_remote(self.target)
            logger.warning(f"Removed from UploadFile: {invalid_state=}")

        return remote_is_valid

    @abstractmethod
    def _confirm_online(self, file: UploadFile) -> bool:
        """Individual checks for each remote"""

    def extract_remote_state(self, file: UploadFile) -> TUploadState:
        """Returns attached UploadState of file, Error if missing"""
        logger.debug(f"start extract: {self.remote_state_cls.__name__}")

        remote_state: RemoteState = file.get_remote_state(self.target)
        if isinstance(remote_state, self.remote_state_cls):
            return remote_state

        raise ValueError(f"{type(remote_state)=},{self.remote_state_cls=}")

    @abstractmethod
    def _upload_local_file(self, file: UploadFile):
        """Upload 1 file and attach remote state to UploadFile"""

    def show_all_files(self):
        """Show all avaliable files on remote"""

        printer.title(f"Fetching files from: {self.print_name}")
        remote_files: list[Any] = self._fetch_all_files()
        printer(remote_files)

        file_descriptions: list[str] = []
        for file in remote_files:
            try:
                file_descriptions.append(
                    self._remote_file_description(file),
                )
            except Exception as e:
                logger.error(f"Problem with {file=}:\n{e}")
                file_descriptions.append("problem...")

        header = f"Files on {self.print_name}: {len(file_descriptions)}"
        title = (  # NOTE: this title better for status?
            f"{self.remote_state_cls.__name__} for files at {self.local_dir}"
        )
        printer.lines_from_list(
            lines=file_descriptions, header=header, title=title
        )

    @abstractmethod
    def _remote_file_description(self, file: Any) -> str:
        """Format remote file for print"""

    def delete_all_uploaded_files(self):
        """Clear remote, may break stored messages for further usage!"""

        remote_files: list[Any] = self._fetch_all_files()
        logger.info("Start deleting files")
        n_deleted = 0

        for file in remote_files:
            n_deleted += 1 if self._rm_remote_file(file) else 0

        if (n_files := len(remote_files)) == n_deleted:
            printer.success(f"Deleted all {n_deleted} of {n_files} files")
        else:
            printer.danger(f"{n_deleted=} but {n_files=}")

    def delete_remote_file(self, identifier: UploadFile) -> bool:
        """Identify remote file with local file and delete"""
        remote_file: Any = self._get_remote_file_by_local_file(identifier)
        if delete_success := self._rm_remote_file(remote_file):
            identifier.touch()
        return delete_success

    @abstractmethod
    def _get_remote_file_by_local_file(self, identifier: UploadFile) -> Any:
        """Identify remote file with local file"""

    @abstractmethod
    def _rm_remote_file(self, remote_file: Any) -> bool:
        """Remove remote file and confirm success"""

    @abstractmethod
    def _get_local_identifier(self, local_files: list[UploadFile]) -> set[str]:
        """Apply unique for each local file for hashable tracking"""

    @abstractmethod
    def _get_local_file_from_identifier(
        self, local_files: list[UploadFile], identifier: set[str]
    ) -> list[UploadFile]:
        """Revert unique for each identifier to get local file back"""

    @abstractmethod
    def _get_remote_identifier(self) -> set[str]:
        """Apply unique for each remote file for hashable tracking"""

    @abstractmethod
    def _get_remote_identifier(self) -> set[str]:
        """Apply unique for each remote file for hashable tracking"""

    @abstractmethod
    def _get_remote_file_from_identifier(
        self, identifier: set[str]
    ) -> list[str]:
        """Revert unique for each identifier to get local file back"""

    def compare_with_remote_files(
        self, local_files: list[UploadFile]
    ) -> CompareResult:

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

        printer.success(f"Statistics for {self.__class__.__name__}")

        # IDEA: function of CompareResult
        frac = f"{len(intersection)}/{n_files}"
        printer.lines_from_list(
            lines=[file.description for file in intersection],
            header=f"Intersection of Local and Remote Files {frac}",
            title=f"Intersection - {self.print_name}",
        )

        frac = f"{len(only_local)}/{n_files}"
        printer.lines_from_list(
            lines=[file.description for file in only_local],
            header=f"Files only in Local registry {frac}",
            title=f"Local - {self.print_name}",
        )

        frac = f"{len(only_remote)}/{n_files}"
        printer.lines_from_list(
            lines=only_remote,
            header=f"Files only in Remote registry {frac}",
            title=f"Global - {self.print_name}",
        )
        return result

    def _delete_not_in_list(self, local_files: list):
        # LATER:
        # REFACTOR: create intersection/difference etc of files
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
