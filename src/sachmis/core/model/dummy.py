from loguru import logger

from sachmis.config.defaults import ModelParam

from ...config import SachmisConfig, get_config
from ...config.models import DummyFamily
from .agent import Model

config: SachmisConfig = get_config()


class DummyModel(Model):
    model: DummyFamily
    param: ModelParam

    def _load_param(self, param: ModelParam | None):
        self.param: ModelParam = param or ModelParam()

    def _load_client(self):
        logger.info("Client prepared")

    def _prepare_chat(self):
        logger.info("Chat prepared")

    def _attach_role(self, role: str):
        logger.debug(role)

    def _attach_prompt(self, prompt: str):
        if not prompt:
            raise FileNotFoundError("Load proper prompt first!")
        logger.debug("loaded prompt")

    def _attach_images(self):
        for i in self.prompt.images:
            logger.info(i)

    def _attach_files(self):
        for i in self.prompt.files:
            logger.info(i)

    def _get_response(self):
        response: str = """blaa
        xxxxx
        xxxxx
        xxxxx
        xxxxx
        xxxxx
        """
        return response

    def _extract_full_response(self) -> str:
        return str(self._raw_response)

    def _extract_response_content(self) -> str:
        return """# content
        bla
        - test
        ## title
        fdsdfsd
        """

    def _extract_response_id(self) -> str:
        return config.timestamp

    def _extract_usage(self) -> dict | None:
        return {"cost": "a lot"}

    def _calculate_usage_cost(self, usage: dict) -> bool:
        _usage = usage
        return False
