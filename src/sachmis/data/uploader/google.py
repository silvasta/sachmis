import time
from typing import Any

from google.genai import Client
from loguru import logger

from ..files.upload import GoogleUploadState, UploadFile
from .base import FileUploader


class GoogleUploader(FileUploader):
    """Specific operations for Google Upload"""

    @property
    def target(self) -> str:
        """Name of remote as defined in UploadFile"""
        return "google"

    def _load_client(self):
        self.client = Client(
            api_key=self._config.from_env(key="GEMINI_API_KEY")
        )

    def _fetch_all_files(self) -> list[Any]:
        """Load all available files from remote registry"""
        return list(self.client.files.list())

    def _upload(self, file: UploadFile) -> GoogleUploadState:
        """Upload 1 file and attach remote state to UploadFile"""

        path = str(self.local_dir / file.local_path)

        if path.endswith((".tex", ".latex")):
            mime_type = "text/plain"
        # LATER: better handling of different files,
        # what was this magic ending detector?
        else:
            mime_type = None

        online_file: Any = self.client.files.upload(
            file=path, config={"mime_type": mime_type}
        )

        double_check = True  # PARAM:
        # LATER: check if... - this is useful - how to extend to xai/base
        if double_check:
            while online_file.state == "PROCESSING":
                logger.debug(f"Waiting for Google to process {file.name}...")
                time.sleep(1)
                # Fetch again to get the updated state
                online_file = self.client.files.get(name=online_file.name)

            if online_file.state == "FAILED":
                logger.error(f"Google failed to process {file.name}")
                raise ValueError(
                    f"File processing failed on remote: {file.name}"
                )

        return self._to_remote_state(online_file)

    def _to_remote_state(self, online_file: Any) -> GoogleUploadState:
        return GoogleUploadState(
            g_uri=online_file.uri,
            g_mime_type=online_file.mime_type,
            g_name=online_file.name,
        )

    def _remove(self, online_file: Any) -> bool:
        try:
            self.client.files.delete(name=online_file.name)
            logger.info(f"Deleted: {online_file.name}")
            return True
        except Exception as e:
            logger.error(e)
            logger.warning(f"Problem with deleting: {online_file.name=}")
            return False
