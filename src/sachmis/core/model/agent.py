from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from ...config import SachmisConfig, get_config
from ...config.defaults import ModelParam
from ...config.models import ModelFamily
from ...data.conversation import Prompt
from ...utils.print import printer
from ..sprout import Sprout

config: SachmisConfig = get_config()


class Model(ABC):
    """Framework + every execution will be done from method here"""

    _raw_response: Any | None = None

    def __init__(self, sprout: Sprout, param: ModelParam | None = None):
        logger.debug(f"Loading {sprout.model.api_name}")

        self.sprout: Sprout = sprout
        self.param: ModelParam = self._load_param(param)

        logger.debug(f"Model ({self.__class__.__name__}) connected with Data")

        self._load_client()
        self._prepare_chat()

        logger.info(f"Model loaded: {self.__class__.__name__}")

    @property
    def model(self) -> ModelFamily:
        return self.sprout.model

    @property
    def has_previous_id(self) -> bool:
        """Look at Sprout and find previous Response ID"""
        return self.sprout.previous_remote_id is not None

    @property
    def prompt(self) -> Prompt:
        """Look at Sprout and find previous Response ID"""
        return self.sprout.prompt

    @abstractmethod
    def _load_param(self, param: ModelParam | None) -> ModelParam:
        """Load defaults if param not set"""

    @abstractmethod
    def _load_client(self, *args, **kwargs):
        """Complete authentication and create Client object"""

    @abstractmethod
    def _prepare_chat(self, *args, **kwargs):
        """Load chat with params defined per Model"""

    def assemble_prompt(self):
        logger.info("Start assembling prompt")
        self.attach_role()
        logger.debug("role attached")
        self._attach_prompt(prompt=self.sprout.prompt.content)
        logger.debug("prompt attached")
        self._attach_images()
        logger.debug("images attached")
        self._attach_files()
        logger.debug("files attached")

    def attach_role(self):
        if role := self.sprout.prompt.role:
            self._attach_role(role.content)
            logger.debug(f"using role: {role.name}")
        else:
            logger.debug("using no role")

    @abstractmethod
    def _attach_role(self, role: str):
        pass

    @abstractmethod
    def _attach_prompt(self, prompt: str):
        pass

    @abstractmethod
    def _attach_images(self):
        pass

    @abstractmethod
    def _attach_files(self):
        pass

    def fire(self):
        """Release prompt and process response"""
        logger.info("Fire")

        self.get_response()
        logger.info("Got response, start processing...")

        self.process_response()

    def get_response(self):
        printer.special(f"Start of Call: {self}")
        self._raw_response: Any = self._get_response()

    @abstractmethod
    def _get_response(self):
        pass

    def process_response(self):
        # raise
        full_response: str = self._extract_full_response()
        self.sprout.collect_raw_response(full_response)

        # maybe raise
        response_id: str = self._extract_response_id()
        content: str = self._extract_response_content()

        printer.success(f"Response Content ({self.model.cli})")
        printer.success(f"Response Content ({self.model.id_cli})")
        printer.md(content)

        # no raise
        usage: dict = self._extract_usage() or {}

        if not self._calculate_usage_cost(usage):
            # Print raw usage, _calculate_usage prints when not failed
            printer(usage)

        self.sprout.collect_response_data(
            content=content,
            remote_id=response_id,
            usage=usage,
        )
        logger.info(f"Response Forwarded: {self.model.unique}")

    @abstractmethod
    def _extract_full_response(self) -> str:
        pass

    @abstractmethod
    def _extract_response_content(self) -> str:
        pass

    @abstractmethod
    def _extract_response_id(self) -> str:
        pass

    @abstractmethod
    def _extract_usage(self) -> dict | None:
        pass

    @abstractmethod
    def _calculate_usage_cost(self, usage) -> bool:
        # TODO: ensure this prints calculate usage
        pass

    # LATER: new methods, e.g.
    # - image receive
    # - chains
    # - MCP
