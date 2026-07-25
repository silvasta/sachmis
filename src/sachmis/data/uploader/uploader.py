from itertools import product

from loguru import logger
from sstcore import System

from ..files.upload import RemoteState, UploadFile
from .base import CompareResult, FileUploader
from .google import GoogleUploader
from .xai import XaiUploader

type RemoteUploader = XaiUploader | GoogleUploader

match_table: dict[str, type[FileUploader]] = {
    "xai": XaiUploader,
    "google": GoogleUploader,
}


def create_single_uploader(
    system: System,
    identifier: str | RemoteState,
) -> type[RemoteUploader]:

    if isinstance(identifier, str):
        target: str = identifier

    elif isinstance(identifier, type(RemoteState)):
        target: str = identifier.target

    else:
        raise ValueError(f"Invalid: {identifier=}, {type(identifier)=}")

    return match_table[target](system)


class Uploader:
    _uploaders: dict[str, RemoteUploader] = {}

    def __init__(self, system: System, xai=False, google=False):
        self.system: System = system
        if xai:
            self.prepare("xai")
        if google:
            self.prepare("google")

    @property
    def clients(self) -> list[RemoteUploader]:
        return list(self._uploaders.values())

    def prepare(self, target: str) -> RemoteUploader:
        """Create Uploader if not cached and provide Instance"""
        if target not in self._uploaders:
            self._uploaders[target] = create_single_uploader(
                self.system, target
            )
            logger.debug(f"Loaded {self._uploaders[target]}")
        return self._uploaders[target]

    def load_files(
        self, files: list[UploadFile], _ensure_after_upload=True
    ) -> list[UploadFile]:  # LATER: check rules for already uploaded files
        """Push Files to Remote and provide confirmed uploaded Files"""

        logger.debug(f"attaching files: {(before := len(files))}")
        uploaded_files: list[UploadFile] = []

        for file, uploader in product(files, self.clients):
            try:
                uploader.upload_file(file)
                uploaded_files.append(file)

            # LATER: check if raise or not

            except FileNotFoundError:
                logger.error(f"Missing {file=}")

            except RuntimeError as err:
                logger.error(f"Upload failed {file=}, {err}")

        logger.debug(f"attached files: {(after := len(files))}")

        if after != before:
            logger.warning(f"Files not perfect: {before=} but { after=}")

        return uploaded_files

    def show_all_files(self):
        for uploader in self.clients:
            uploader.show_all_files()

    def compare_with_remote_files(self, files: list[UploadFile]):
        for uploader in self.clients:
            # FIX::
            _result: CompareResult = uploader.compare_with_remote_files(files)

    def delete_all_uploaded_files(self):
        for uploader in self.clients:
            uploader.delete_all_uploaded_files()
