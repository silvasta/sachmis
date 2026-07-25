from typing import Any

from loguru import logger
from xai_sdk import Client

from ..files.upload import UploadFile, XaiUploadState
from .base import FileUploader


class XaiUploader(FileUploader):
    """Specific operations for xAI Upload"""

    @property
    def target(self) -> str:
        return "xai"

    @property
    def remote_state_cls(self) -> type[XaiUploadState]:
        """Derived class of UploadState"""
        return XaiUploadState

    def _load_client(self):
        self.client = Client(api_key=self._config.from_env(key="XAI_API_KEY"))

    def _fetch_all_files(self) -> list[Any]:
        # NOTE: how is this refreshed here at second load?
        files: Any = self.client.files.list()
        return files.data

    def _upload(self, file: UploadFile) -> XaiUploadState:
        path = str(self.local_dir / file.local_path)
        online_file = self.client.files.upload(path)
        return self._to_remote_state(online_file)

    def _to_remote_state(self, online_file: Any) -> XaiUploadState:
        return XaiUploadState(x_id=online_file.id)

    def _remove(self, online_file: Any) -> bool:
        delete_response: Any = self.client.files.delete(online_file.id)
        if delete_response.deleted:
            name: str = online_file.filename
            logger.info(f"Deleted: {delete_response.id} - {name}")
            return True
        else:
            logger.error(f"Problem with deleting: {delete_response=}")
            return False
