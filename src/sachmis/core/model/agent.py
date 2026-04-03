from abc import ABC, abstractmethod
from pathlib import Path

from loguru import logger

from sachmis.config.manager import config
from sachmis.config.model import ModelFamily
from sachmis.data import DataManager
from sachmis.data.arboreal import Sprout
from sachmis.data.files import Prompt, Response
from sachmis.utils.print import printer


class Model(ABC):
    """Framework + every execution will be done from method here"""

    previous_response_id: str | None = None

    def __init__(
        self,
        data: DataManager,
        model: ModelFamily,
        tree_locator: str = "",
    ):
        logger.debug(f"Loading {model.api_name}")

        self.data: DataManager = data
        self.model: ModelFamily = model
        self.old_tree_locator = tree_locator

        # NOTE: use Tree here?
        self.sprout: Sprout = self.data.attach(
            # TEST: handover the tree_locator here?
            model,
            tree_locator=tree_locator,
        )
        # TODO:attach previous response id, see Grok
        logger.debug("Model connected with Data")

        self._load_client()
        self._prepare_chat()
        logger.debug("Client loaded, Chat prepared")

    @abstractmethod
    def _load_client(self, *args, **kwargs):
        """Complete authentification and create Client object"""

    @property
    def prompt(self) -> Prompt:
        return self.sprout.prompt

    @property
    def response(self) -> Response | None:
        return self.sprout.response

    @abstractmethod
    def _prepare_chat(self, *args, **kwargs):
        pass

    def assemble_prompt(self):
        logger.info("Start assembling prompt")
        self._attach_role()
        self._attach_prompt()
        self._attach_images()
        self._attach_files()

    @abstractmethod
    def _attach_role(self):
        pass

    @abstractmethod
    def _attach_prompt(self):
        pass

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
        self._response = self._get_response()

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
        self.data.biome.attach_new_full_response(
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
