import time
from typing import Any

from loguru import logger

from sachmis.config import SachmisConfig, get_config
from sachmis.data.files import GoogleUploadState, UploadFile

from .uploader import FileUploader

config: SachmisConfig = get_config()


class GoogleUploader(FileUploader):
    """Specific operations for Google Upload"""

    @property
    def target(self) -> str:
        """Name of remote as defined in UploadFile"""
        return "google"

    @property
    def print_name(self) -> str:
        """Name of remote styled for print"""
        return "Google"

    @property
    def remote_state_cls(self) -> type[GoogleUploadState]:
        """Derived class of UploadState"""
        return GoogleUploadState

    def _load_client(self):
        from google.genai import Client

        self.client = Client(api_key=config.from_env(key="GEMINI_API_KEY"))
        logger.info("Google Client loaded")

    def _fetch_all_files(self) -> list[Any]:
        """Load all avaliable files from remote registry"""
        # WARN: how is this refreshed here?
        # - load client again?
        return self.client.files.list()

    def _confirm_online(self, file: UploadFile) -> bool:
        """Check if file is not outdated"""
        remote_state: GoogleUploadState = self.extract_remote_state(file)
        return not remote_state.is_outdated

    def _upload_local_file(self, file: UploadFile) -> GoogleUploadState:
        """Upload 1 file and attach remote state to UploadFile"""

        path = str(self.local_dir / file.local_path)
        mime_type = None

        if path.endswith((".tex", ".latex")):
            mime_type = "text/plain"

        # LATER: better handling of different files,
        # what was this magic ending detector?

        remote_file: Any = self.client.files.upload(
            file=path, config={"mime_type": mime_type}
        )

        double_check = True  # PARAM:
        # LATER: check if...
        # - this is useful
        # - how to extend to xai/base
        if double_check:
            while remote_file.state == "PROCESSING":
                logger.debug(f"Waiting for Google to process {file.name}...")
                time.sleep(1)
                # Fetch again to get the updated state
                remote_file = self.client.files.get(name=remote_file.name)

            if remote_file.state == "FAILED":
                logger.error(f"Google failed to process {file.name}")
                raise ValueError(
                    f"File processing failed on remote: {file.name}"
                )

        mime_type = remote_file.mime_type
        logger.success(f"Uploaded to Google: {file.name} with {mime_type=}")

        return GoogleUploadState(
            g_uri=remote_file.uri,
            g_mime_type=remote_file.mime_type,
            g_name=remote_file.name,
        )

    def _remote_file_description(self, file: Any) -> str:
        """Format remote file for print"""
        return f"{file.uri} - {file.name}"

    def _get_remote_file_by_local_file(self, identifier: UploadFile) -> Any:
        """Identify remote file with local file"""
        remote_state: GoogleUploadState = self.extract_remote_state(identifier)
        return self.client.files.get(name=remote_state.g_name)

    def _rm_remote_file(self, remote_file: Any) -> bool:
        """Remove remote file and confirm success"""
        try:
            self.client.files.delete(name=remote_file.name)
            logger.info(f"Deleted: {remote_file.name}")
            return True
        except Exception as e:
            logger.error(e)
            logger.warning(f"Problem with deleting: {remote_file.name=}")
            return False

    def _get_local_identifier(self, local_files: list[UploadFile]) -> set[str]:
        """Apply unique for each local file for hashable tracking"""
        identifier: set[str] = set()
        for file in local_files:
            if file.has_remote(self.target):
                identifier.add(self.extract_remote_state(file).g_name)
        return identifier

    def _get_local_file_from_identifier(
        self, local_files: list[UploadFile], identifier: set[str]
    ) -> list[UploadFile]:
        """Revert unique for each identifier to get local file back"""
        return [
            file
            for file in local_files
            if file.has_remote(self.target)
            if self.extract_remote_state(file).g_name in identifier
        ]

    def _get_remote_identifier(self) -> set[str]:
        """Apply unique for each remote file for hashable tracking"""
        return set(file.name for file in self.get_remote_files())

    def _get_remote_file_from_identifier(
        self, identifier: set[str]
    ) -> list[str]:
        """Revert unique for each identifier to get remote file back"""
        return [
            self._remote_file_description(file)
            for file in self.get_remote_files()
            if file.name in identifier
        ]
