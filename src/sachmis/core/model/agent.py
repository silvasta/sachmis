from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from loguru import logger
from tenacity import (
    Retrying,
    before_sleep_log,
    # retry,
    stop_after_attempt,
    wait_exponential,
)

from ...config import SachmisConfig, get_config
from ...config.defaults import ModelParam, TenacityDefaults
from ...config.models import ModelFamily
from ...data import DataManager
from ...data.conversation import Response
from ...exceptions import SachmisDataError
from ...utils.print import printer
from .. import retry

config: SachmisConfig = get_config()


# def retry_tenacity():
#     """Test 1"""
#     td: TenacityDefaults = config.defaults.tenacity
#
#     return retry(
#         stop=stop_after_attempt(td.max_attempts),
#         wait=wait_exponential(**td.wait_exponential),
#         before_sleep=before_sleep_log(logger, log_level=20),
#         reraise=True,
#     )


class Model(ABC):
    """Framework + every execution will be done from method here"""

    _raw_response: Any | None = None
    _response: Response | None = None

    def __init__(
        self,
        model: ModelFamily,
        data: DataManager,
        param: ModelParam | None = None,
    ):
        logger.debug(f"Loading {model.api_name}")

        self.model: ModelFamily = model
        self.data: DataManager = data
        self.param: ModelParam = self._load_param(param)

        logger.debug(f"Model ({self.__class__.__name__}) connected with Data")

        self._load_client()
        self._prepare_chat()

        logger.info(f"Model loaded: {self.__class__.__name__}")

    @abstractmethod
    def _load_param(self, param: ModelParam | None) -> ModelParam:
        """Load defaults if param not set"""

    @abstractmethod
    def _load_client(self, *args, **kwargs):
        """Complete authentication and create Client object"""

    @property
    def response(self) -> Response:
        if self._response is None:
            raise SachmisDataError("Response not already arrived...")
        return self._response

    @abstractmethod
    def _prepare_chat(self, *args, **kwargs):
        """Load chat with params defined per Model"""

    def assemble_prompt(self):
        logger.info("Start assembling prompt")
        self.attach_role()
        logger.debug("role attached")
        self._attach_prompt(prompt=self.data.handler.prompt.content)
        logger.debug("prompt attached")
        self._attach_images()
        logger.debug("images attached")
        self._attach_files()
        logger.debug("files attached")

    def attach_role(self):
        if role := self.data.handler.prompt.role:
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

    def fire_retry(self):
        """Test 2"""
        logger.info("Fire")

        td: TenacityDefaults = config.defaults.tenacity

        retryer = Retrying(
            stop=stop_after_attempt(td.max_attempts),
            wait=wait_exponential(**td.wait_exponential),
            before_sleep=before_sleep_log(logger, log_level=2),
            reraise=True,
        )
        for attempt in retryer:
            with attempt:
                self._raw_response: Any = self._get_response()

        logger.info("Got response, start processing...")
        self.process_response()

    def fire(self):
        """Release prompt and process response"""
        logger.info("Fire")

        self._count = 0
        self.get_response()
        logger.info("Got response, start processing...")

        self.process_response()

    @retry.relaxed()
    def get_response(self):
        self._count += 1
        logger.debug(f"Start of try {self._count}")
        self._raw_response: Any = self._get_response()

    @abstractmethod
    def _get_response(self):
        pass

    def process_response(self):
        # raise
        full_response: str = self._extract_full_response()

        full_response_path: Path = config.paths.full_response(
            topic=self.data.handler.prompt.topic, model=self.model.unique
        )
        self.data._add_temporary_full_response(
            text=full_response, path=full_response_path
        )

        # maybe raise
        response_id: str = self._extract_response_id()
        content: str = self._extract_response_content()

        printer.success(f"Response Content ({self.model.unique})")
        printer.md(content)

        # no raise
        usage: dict = self._extract_usage() or {}

        if not self._calculate_usage_cost(usage):
            printer(usage)

        response: Response = Response.from_model(
            content=content,
            model=self.model.unique,
            remote_id=response_id,
            usage=usage,
            full_response=full_response_path,
            topic=self.data.handler.prompt.topic,
        )
        self.data.handle_response(response)
        logger.info(f"Response processed: {self.model.unique}")

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
