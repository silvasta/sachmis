from abc import ABC, abstractmethod

from loguru import logger

from sachmis.config.model import ModelFamily
from sachmis.data import DataManager
from sachmis.utils.print import printer


class Model(ABC):
    """Framework + every execution will be done from method here"""

    # TASK: handle this otherwise
    # - consider: subclass works already with this
    previous_response_id: str | None = None

    def __init__(
        self,
        data: DataManager,
        model: ModelFamily,
        topic: str | None = None,
    ):
        # self.data: DataManager = data
        self.model: ModelFamily = model
        self.topic: str | None = topic

    def _boot(self):
        """Shared startup logic After base and subclass init"""
        self._load_client()

        # TODO: provide this in subclass? remove _boot?
        self.previous_response_id: str = self.data.get_previous_id(self.model)

        self._prepare_chat()
        self.assemble_prompt()

    @abstractmethod
    def _load_client(self, *args, **kwargs):
        """Complete authentification and create Client object"""
        pass

    @abstractmethod
    def _prepare_chat(self, *args, **kwargs):
        pass

    def assemble_prompt(self):
        logger.info("Start assembling prompt")
        self._attach_role()
        self._attach_prompt()  # TODO: global verify prompt is avaliable?
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

    @abstractmethod
    def fire(self):
        """Release prompt and process response"""

        logger.info("Fire")
        self._get_response()

        logger.info("Got response, start processing...")
        self.process_response()

    @abstractmethod
    def _get_response(self):
        pass

    def process_response(self):
        self._extract_full_response()
        printer.title(f"Response Content ({self.model.unique})", style="write")
        self._extract_response_content()
        # TODO: check how to move printer(XXX) here makes sense
        self._extract_usage()
        self._calculate_usage_cost()
        self._setup_response_data()
        logger.info(f"End of {self.model}")

    @abstractmethod
    def _extract_full_response(self):
        pass

    @abstractmethod
    def _extract_response_content(self):
        pass

    @abstractmethod
    def _extract_response_id(self):
        pass

    @abstractmethod
    def _extract_usage(self):
        pass

    @abstractmethod
    def _calculate_usage_cost(self):
        pass

    @abstractmethod
    def _setup_response_data(self):
        pass

    # LATER: new methods, e.g.
    # - image receive
    # - chains
    # - MCP
