from typing import Any

from loguru import logger

from sachmis.config import SachmisConfig, get_config
from sachmis.data.files import UploadFile, XaiUploadState

from .uploader import FileUploader

config: SachmisConfig = get_config()


class XaiUploader(FileUploader):
    """Specific operations for xAI Upload"""

    @property
    def target(self) -> str:
        """Name of remote as defined in UploadFile"""
        return "xai"

    @property
    def print_name(self) -> str:
        """Name of remote styled for print"""
        return "xAI"

    @property
    def remote_state_cls(self) -> type[XaiUploadState]:
        """Derived class of UploadState"""
        return XaiUploadState

    def _load_client(self):
        from xai_sdk import Client

        self.client = Client(api_key=config.from_env(key="XAI_API_KEY"))
        logger.info("xAI Client loaded")

    def _fetch_all_files(self) -> list[Any]:
        """Load all avaliable files from remote registry"""
        # WARN: how is this refreshed here at second load?
        files: Any = self.client.files.list()
        return files.data  # NOTE: why data?

    def _confirm_online(self, file: UploadFile) -> bool:
        """Load online registry and check if file is there"""
        remote_state: XaiUploadState = self.extract_remote_state(file)
        return remote_state.x_id in self._get_remote_identifier()

    def _upload_local_file(self, file: UploadFile):
        """Upload 1 file and attach remote state to UploadFile"""

        path = str(self.local_dir / file.local_path)
        online_file: Any = self.client.files.upload(path)

        logger.success(f"Uploaded to xAI: {file.name}")

        return XaiUploadState(x_id=online_file.id)

    def _remote_file_description(self, file: Any) -> str:
        """Format remote file for print"""
        return f"{file.id} - {file.filename}"

    def _get_remote_file_by_local_file(self, identifier: UploadFile) -> Any:
        """Identify remote file with local file"""
        remote_state: XaiUploadState = self.extract_remote_state(identifier)
        return self.client.files.get(remote_state.x_id)

    def _rm_remote_file(self, remote_file: Any) -> bool:
        """Remove remote file and confirm success"""
        delete_response: Any = self.client.files.delete(remote_file.id)
        if delete_response.deleted:
            name: str = remote_file.filename
            logger.info(f"Deleted: {delete_response.id} - {name}")
            return True
        else:
            logger.error(f"Problem with deleting: {delete_response=}")
            return False

    def _get_local_identifier(self, local_files: list[UploadFile]) -> set[str]:
        """Apply unique for each local file for hashable tracking"""
        identifier: set[str] = set()
        for file in local_files:
            if file.has_remote(self.target):
                identifier.add(self.extract_remote_state(file).x_id)
        return identifier

    def _get_local_file_from_identifier(
        self, local_files: list[UploadFile], identifier: set[str]
    ) -> list[UploadFile]:
        """Revert unique for each identifier to get local file back"""
        return [
            file
            for file in local_files
            if file.has_remote(self.target)
            and self.extract_remote_state(file).x_id in identifier
        ]

    def _get_remote_identifier(self) -> set[str]:
        """Apply unique for each remote file for hashable tracking"""
        return set(
            file.id  # FIX: load registry every time?
            for file in self.get_remote_files()
        )

    def _get_remote_file_from_identifier(
        self, identifier: set[str]
    ) -> list[str]:
        """Revert unique for each identifier to get remote file back"""
        return [
            self._remote_file_description(file)
            for file in self.get_remote_files()
            if file.id in identifier
        ]
