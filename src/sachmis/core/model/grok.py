from google.protobuf import json_format
from loguru import logger
from xai_sdk import Client
from xai_sdk.chat import Response, file, image, system, user
from xai_sdk.sync.chat import Chat

from ...config import config
from ...config.defaults import GrokParam, ModelParam
from ...config.models import Groks
from ...data.files import XaiUploadState
from ...exceptions import SachmisDataError
from .agent import Model


class Grok(Model):
    model: Groks
    param: GrokParam
    client: Client
    chat: Chat
    _raw_response: Response

    def _load_param(self, param: ModelParam | None) -> GrokParam:
        """Load defaults if param not set"""
        # LATER: centralize
        if param is None:
            param: GrokParam = config().defaults.grok
        if isinstance(param, GrokParam):
            return param
        # LATER: imprve
        raise SachmisDataError(f"{self.__class__.__name__}: Invalid {param=}")

    def _load_client(self):
        self.client = Client(
            api_key=config().from_env(key="XAI_API_KEY"),
            timeout=self.param.timeout,
        )

    def _prepare_chat(self):
        param: dict = {
            "model": self.model.api_name,
            "store_messages": self.param.store_messages,
        }
        if id := self.sprout.previous_remote_id:
            logger.debug("got locator")
            param |= {"previous_response_id": id}
            logger.info(f"{self.model} attaches previous response with: {id=}")

        if self.model == Groks.G420M:
            param |= {"agent_count": self.param.n_agents}

        logger.debug(f"{param=}")
        self.chat: Chat = self.client.chat.create(**param)

    def _attach_role(self, role: str):
        self.chat.append(system(role))

    def _attach_prompt(self, prompt: str):
        self.chat.append(user(prompt))

    def _attach_images(self):
        # TASK: check image input again, base64 still needed?
        # - create structure to collect used images
        # - input images/FILES from file/pick/list/folder?
        for i in self.prompt.images:
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
        for upload_file in self.prompt.files:
            state = upload_file.get_remote_state(self.model.target)
            if isinstance(state, XaiUploadState):
                self.chat.append(user(file(state.x_id)))
                logger.debug(f"loaded: {upload_file.name=}, {state.x_id}")
            else:
                logger.warning(f"Failed: {upload_file=}")

    def _get_response(self):
        response: Response = self.chat.sample()
        return response

    def _extract_full_response(self) -> str:
        try:
            return str(self._raw_response)
        except Exception as e:
            logger.error(f"Error for response: {self.model.api_name}\n{e}")
            raise

    def _extract_response_content(self) -> str:
        try:
            return self._raw_response.content
        except Exception as e:
            logger.error(f"Error for content: {self.model.api_name}\n{e}")
            raise

    def _extract_response_id(self) -> str:
        try:
            return self._raw_response.id
        except Exception as e:
            logger.error(f"Error for ID: {self.model.api_name}\n{e}")
            return "FAIL"

    def _extract_usage(self) -> dict | None:
        try:
            return json_format.MessageToDict(self._raw_response.usage)
        except Exception as e:
            logger.error(f"Usage {self.model.unique}:\n{e}")
            return None

    def _calculate_usage_cost(self, usage: dict) -> bool:
        try:
            # TODO: ensure this prints calculate usage
            self.model.usage_cost(token_usage=usage)
            return True
        except Exception as e:
            logger.error(f"Usage calculation {self.model.unique}: {e}")
            return False
