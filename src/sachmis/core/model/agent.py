from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from loguru import logger

from sachmis.config.defaults import ModelParam

from ...config import SachmisConfig, get_config
from ...config.model import ModelFamily
from ...data import DataManager, Prompt, Response
from ...data.arboreal import Sprout, Tree
from ...utils.print import printer

config: SachmisConfig = get_config()


class Model(ABC):
    """Framework + every execution will be done from method here"""

    _raw_response: Any | None = None

    def __init__(
        self,
        model: ModelFamily,
        data: DataManager,
        param: ModelParam,
        tree: Tree,
        sprout: Sprout,
    ):
        logger.debug(f"Loading {model.api_name}")

        self.model: ModelFamily = model
        self.data: DataManager = data
        self.param: ModelParam = param
        self.read_only_tree: Tree = tree
        self.sprout: Sprout = sprout

        logger.debug(f"Model ({self.__class__.__name__}) connected with Data")

        self._load_client()
        self._prepare_chat()

        logger.info(f"Model loaded: {self.__class__.__name__}")

    @abstractmethod
    def _load_client(self, *args, **kwargs):
        """Complete authentification and create Client object"""

    @property
    def prompt(self) -> Prompt:
        return self.sprout.prompt

    @property
    def response(self) -> Response | None:
        return self.sprout.response

    def find_previous_sprout(self) -> Sprout | None:
        return self.read_only_tree.find_previous_sprout(self.sprout)

    def previous_response_id(self) -> str | None:
        if (previous := self.find_previous_sprout()) is None:
            logger.debug("previous_sprout not found")
            return None
        if previous.response is None:
            logger.error("FAIL: Previous Sprout without Response??")
            return None
        return previous.response.id

    @abstractmethod
    def _prepare_chat(self, *args, **kwargs):
        """Load chat with params defined per Model"""

    def assemble_prompt(self):
        logger.info("Start assembling prompt")
        self.attach_role()
        self._attach_prompt(prompt=self.sprout.load_prompt_text())
        self._attach_images()
        self._attach_files()

    def attach_role(self):
        if role := self.data._role:
            self._attach_role(role)
            logger.debug(f"using role: {self.data._role_path.name}")
        else:
            logger.debug("using no role")

    @abstractmethod
    def _attach_role(self, role: str):
        pass

    @abstractmethod
    def _attach_prompt(self, prompt: str):
        pass

    def _get_prompt_text(self) -> str:  # MOVE: to sprout?
        if not (prompt := self.prompt.text):
            raise FileNotFoundError("Load proper prompt first!")
        self.sprout.set_loaded()
        return prompt

    @abstractmethod
    def _attach_images(self):
        # TASK: check image input again, base64 still needed?
        # - create structure to collect used images
        # - input images/FILES from file/pick/list/folder?
        pass

    @abstractmethod
    def _attach_files(self):
        pass

    def fire(self):
        """Release prompt and process response"""

        logger.info("Fire")
        self.sprout.set_started()
        self._raw_response: Any = self._get_response()

        logger.info("Got response, start processing...")
        self.process_response()

    @abstractmethod
    def _get_response(self):
        pass

    def process_response(self):
        # raise
        full_response: str = self._extract_full_response()

        full_response_path: Path = config.paths.full_response(
            topic=self.prompt.topic, model=self.model.unique
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
            # TODO: ensure this prints calculate usage
            printer(usage)

        response = Response(
            full_response=full_response_path,
            id=response_id,
            content=content,
            usage=usage,
        )
        self.sprout.response: Response = response
        logger.info(f"Response processed: {self.model}")

        self.data.handle_response(self.sprout)

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
