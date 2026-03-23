from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from loguru import logger

from ..config.manager import config
from ..utils.print import printer
from .files import File


class FileUploader(ABC):
    client: Any

    @abstractmethod
    def upload_local_file(self, file: File, base_path: Path):
        pass

    @abstractmethod
    def show_all_files(self):
        pass

    @abstractmethod
    def delete_all_uploaded_files(self):
        pass


class GoogleUploader(FileUploader):
    def __init__(self):
        from google.genai import Client

        self.client = Client(
            api_key=ConfigManager.from_env(key="GEMINI_API_KEY")
        )
        logger.info("Google Client loaded")

    def upload_local_file(self, file: File, base_path: Path):
        if file.g_uri is not None:
            logger.info(f"{file.name=} already uploaded")
            # return
        path = str(base_path / file.local_path)

        mime_type = None
        if path.endswith((".tex", ".latex")):
            mime_type = "text/plain"
        # Pass the mime_type to the upload method
        online_file: Any = self.client.files.upload(
            file=path, config={"mime_type": mime_type}
        )
        file.g_uri = online_file.uri
        file.g_mime_type = online_file.mime_type
        logger.success(
            f"File uploaded to Google: {file.name} as {file.g_mime_type}"
        )

    def show_all_files(self):
        files: Any = self.client.files.list()
        printer.print(files)
        try:
            printer.success(f"Total: {len(files)}")
        except Exception as e:
            logger.error(f"Not possible to get length: {e}")

    def delete_all_uploaded_files():
        # NOTE: Google: delete uploaded, altough... automatic in 48 hours
        pass


class XaiUploader(FileUploader):
    def __init__(self):
        from xai_sdk import Client

        self.client = Client(api_key=ConfigManager.from_env(key="XAI_API_KEY"))
        logger.info("xAI Client loaded")

    def upload_local_file(self, file: File, base_path: Path):
        # TODO: check this in base class
        if file.x_id is not None:
            # WARN: check if online file valid
            logger.info(f"{file.name=} already uploaded")
            return
        path = str(base_path / file.local_path)
        online_file: Any = self.client.files.upload(path)

        file.x_id: str = online_file.id
        logger.success(f"File uploaded to xAI: {file.name}")

    def show_all_files(self):
        files: Any = self.client.files.list()
        printer.print(files)
        try:
            printer.success(f"Total: {len(files.data)}")
            for file in files.data:
                printer.md(f"{file.id} - {file.filename}\n")
        except Exception as e:
            logger.error(f"Not possible to get length: {e}")

    def compare_with_list(self, local_files: list[File]):
        online_files: Any = self.client.files.list()

        in_list = []
        not_in_list = []
        local_ids = set(
            file.x_id for file in local_files if file.x_id is not None
        )
        for online_file in online_files.data:
            if online_file.id in local_ids:
                in_list.append(online_file)
            else:
                not_in_list.append(online_file)

        # printer.title("Files in local and online files", style="green")
        # printer.print(in_list)
        # printer.title("Online Files not in Local files", style="red")
        # printer.print(not_in_list)

        printer.title("Final statistic - Online in Local")
        printer.print(f"{len(local_files)=}")
        printer.print(f"{len(in_list)=}")
        printer.print(f"{len(not_in_list)=}")

        # TODO: refactor file comparison
        # TODO: def confirm_uploaded() that also uploads if necessacry

        in_list = []
        not_in_list = []
        online_ids = set(file.id for file in online_files.data)
        for local_file in local_files:
            if local_file.x_id in online_ids:
                in_list.append(local_file)
            else:
                not_in_list.append(local_file)

        # printer.title("Files in local and online files", style="green")
        # printer.print(in_list)
        # printer.title("Local Files not in Onlne files", style="red")
        # printer.print(not_in_list)

        printer.title("Final statistic - Local in Online")
        printer.print(f"{len(local_files)=}")
        printer.print(f"{len(in_list)=}")
        printer.print(f"{len(not_in_list)=}")

        if len(local_files) == len(in_list):
            return True
        else:
            return False

    def delete_not_in_list(self, local_files: list[File]):
        online_files: Any = self.client.files.list()
        local_ids = set(
            file.x_id for file in local_files if file.x_id is not None
        )
        for online_file in online_files.data:
            if online_file.id in local_ids:
                logger.success(f"file confirmed: {online_file.filename}")
            else:
                self.delete_one_file(online_file)

    def delete_one_file(self, file) -> bool:
        delete_response: Any = self.client.files.delete(file.id)
        printer.print(f"Deleting File: {file.filename}")
        if delete_response.deleted:
            logger.info(f"Deleted: {delete_response.id}")
            return True
        else:
            logger.error(f"Problem deleting: {delete_response.id}")
            return False

    def delete_all_uploaded_files(self):
        files: Any = self.client.files.list()
        logger.info("Start deleting files")
        try:
            n_deleted = 0
            for file in files.data:
                n_deleted += 1 if self.delete_one_file(file) else 0
            printer.success(f"Deleted {n_deleted} of {len(files.data)}")
        except Exception as e:
            logger.error(f"Not possible to delete files:\n{e}")
