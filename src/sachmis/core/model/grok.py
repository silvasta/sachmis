from google.protobuf import json_format
from loguru import logger
from xai_sdk import Client
from xai_sdk.chat import Response, image, system, user
from xai_sdk.sync.chat import Chat

from sachmis.config import SachmisConfig, get_config
from sachmis.config.model import Groks
from sachmis.data import DataManager

from .agent import Model

config: SachmisConfig = get_config()


class Grok(Model):
    model: Groks
    client: Client
    chat: Chat
    response: Response

    def __init__(
        self,
        data: DataManager,
        model: Groks,
        tree_locator: str = "",
        timeout: int = 3600,
        store_messages: bool = True,
    ):

        # TODO: grok default config to config.defaults
        self.timeout: int = timeout
        self.store_messages: bool = store_messages

        # INFO: super() after storing variables for:
        # - self._load_client()
        # - data.attach()
        logger.debug(f"{tree_locator=}")
        super().__init__(data, model, tree_locator)

    def _load_client(self):
        self.client = Client(
            api_key=config.from_env(key="XAI_API_KEY"),
            timeout=self.timeout,
        )

    def _prepare_chat(self):
        param: dict = {
            "model": self.model.api_name,
            "store_messages": self.store_messages,
        }
        # NEXT: check in model.agent
        if self.old_tree_locator:
            logger.debug("got locator")
            previous_response_id: str = self.data.find_previous_id(
                self.old_tree_locator
            )
            param |= {
                "previous_response_id": previous_response_id,
            }
            logger.info(f"{self.model} using {previous_response_id=}")
        self.chat: Chat = self.client.chat.create(**param)
        logger.debug(f"{param=}")

    def _attach_role(self):
        if role := self.data._role:
            self.chat.append(system(role))
        logger.debug(role)

    def _attach_prompt(self):

        if not (prompt := self.prompt.text):
            raise FileNotFoundError("Load proper prompt first!")

        self.chat.append(user(prompt))
        logger.debug(prompt)

    def _attach_images(self):
        for i in self.data._images:
            # FIX: apply base64 transform
            self.chat.append(
                user(image(image_url=f"data:image/jpeg;base64,{i}"))
                # LATER: jpeg? worked with png but clarify somewhen
            )

    # def load_input_image(self, image_path: Path) -> None:
    #     """So far, encoding image to base64 string"""
    #
    #     # b64 string images loading for grok
    #     if image := load_b64_and_encode(image_path):
    #         self.base64_images.append(image)
    #     else:
    #         logger.warning(f"Base 64 image loading failed: {image_path}")

    def _attach_files(self):
        # FIX:
        # x = XaiUploader()  # MOVE: do this in data
        # if len(self.data._files) > 0:
        #     if x.compare_with_list(self.data._files):
        #         logger.success("Files confirmed online")
        #     else:
        #         raise FileNotFoundError(
        #             "Check uploads, at least 1 file not online!"
        #         )
        # for local_file in self.data.files:  # REMOVE: verification in data
        #     if local_file.x_id is None:
        #         logger.warning(f"Ignoring {local_file.name}, no valid x_id!")
        #     else:
        #         self.chat.append(user(file(local_file.x_id)))
        #         logger.debug(
        #             f"loaded file: {local_file.topic=}, {local_file.name}, {local_file.x_id}"
        #         )
        pass

    # @retry( # IMPORTANT: retry
    #     stop=stop_after_attempt(config.defaults.tenacity.max_attempts),
    #     wait=wait_exponential(**config.defaults.tenacity.wait_exponential),
    #     # TODO: before_sleep=before_sleep_log(logger, logging.WARNING)
    # )
    def _get_response(self):
        self.raise_error = False  # REMOVE:
        response: Response = self.chat.sample()
        return response

    def _extract_full_response(self) -> str:
        try:
            return str(self._response)
        except Exception as e:
            logger.error(f"Error for response: {self.model.api_name}\n{e}")
            if not self.raise_error:  # REMOVE:
                return "no response"
            raise

    def _extract_response_content(self) -> str:
        try:
            return self._response.content
        except Exception as e:
            logger.error(f"Error for content: {self.model.api_name}\n{e}")
            if not self.raise_error:  # REMOVE:
                return "no content"
            raise

    def _extract_response_id(self) -> str:
        try:
            return self._response.id
        except Exception as e:
            logger.error(f"Error for ID: {self.model.api_name}\n{e}")
            if not self.raise_error:  # REMOVE:
                return "no id"
            raise

    def _extract_usage(self) -> dict | None:
        try:
            return json_format.MessageToDict(self._response.usage)
        except Exception as e:
            logger.error(f"Usage {self.model.unique}:\n{e}")
            return None

    def _calculate_usage_cost(self, usage: dict) -> bool:
        try:
            # TODO: ensure this prints calculate usage
            self.model.usage_cost(token_usage=usage)
            return True
        except Exception as e:
            logger.error(f"Usage calculcation {self.model.unique}: {e}")
            return False
