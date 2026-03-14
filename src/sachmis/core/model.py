from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from .data import DataManager
from .models import Models


class Model(ABC):
    data: DataManager
    model: Models
    topic: str | None
    previous_response_id: str | None = None
    client: Any = None
    chat: Any = None

    def __init__(self, data: DataManager, model: Models, topic: str | None = None):
        self.data: DataManager = data
        self.model: Models = model
        self.topic: str | None = topic

    def _boot(self):
        """Shared logic at startup"""
        self.load_client()
        self.previous_response_id: str = self.data.get_previous_id(self.model)

        self.prepare_chat()

        logger.info("Start assembling prompt")
        self.assemble_prompt()

    @abstractmethod
    def load_client(self, *args, **kwargs):
        """Complete authentification and create Client object"""
        pass

    @abstractmethod
    def prepare_chat(self, *args, **kwargs):
        pass

    def assemble_prompt(self):
        self.attach_role()
        self.attach_prompt()
        self.attach_images()
        # TODO: write the file somewhere
        self.attach_files()

    @abstractmethod
    def attach_role(self):
        pass

    @abstractmethod
    def attach_prompt(self):
        pass

    @abstractmethod
    def attach_images(self):
        pass

    @abstractmethod
    def attach_files(self):
        pass

    @abstractmethod
    def fire(self):
        pass

    @abstractmethod
    def process_response(self):
        pass

    # TODO: new methods, e.g. image receive
