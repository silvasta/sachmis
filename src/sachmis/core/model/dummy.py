from loguru import logger

from sachmis.config.defaults import ModelParam

from ...config import SachmisConfig, get_config
from ...config.model.dummy import DummyFamily
from .agent import Model

config: SachmisConfig = get_config()

# NEXT: models


class DummyModel(Model):
    model: DummyFamily
    param: ModelParam

    def _load_client(self):
        logger.info("Client prepared")

    def _prepare_chat(self):
        logger.info("Chat prepared")

    def _attach_role(self):
        if role := self.data._role:
            logger.debug(role)

    def _attach_prompt(self):

        if not (prompt := self.prompt.text):
            raise FileNotFoundError("Load proper prompt first!")
        logger.debug(prompt)

    def _attach_images(self):
        for i in self.data._images:
            logger.info(i)

    def _attach_files(self):
        for i in self.data._files:
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
        return False
