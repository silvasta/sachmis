from google.protobuf import json_format
from loguru import logger
from xai_sdk import Client
from xai_sdk.chat import Response, file, image, system, user
from xai_sdk.sync.chat import Chat

from sachmis.config.manager import config
from sachmis.config.model import Groks
from sachmis.data import DataManager
from sachmis.data.uploader import XaiUploader  # REMOVE: -> data
from sachmis.utils.print import printer

from .agent import Model


class Grok(Model):
    model: Groks
    client: Client
    chat: Chat
    response: Response

    def __init__(
        self,
        data: DataManager,
        model: Groks,
        topic: str | None = None,
        timeout: int = 3600,
        store_messages: bool = True,
    ):
        super().__init__(data, model, topic)

        self.timeout: int = timeout
        self.store_messages: bool = store_messages

        self._boot()

    def load_client(self):
        self.client = Client(
            api_key=config.from_env(key="XAI_API_KEY"),
            timeout=self.timeout,
        )
        logger.debug("Client loaded")

    def prepare_chat(self):
        param: dict = {
            "model": self.model.api_name,
            "store_messages": self.store_messages,
        }
        if self.previous_response_id:
            param |= {
                "previous_response_id": self.previous_response_id,
            }
            logger.debug(f"{self.model} using {self.previous_response_id=}")
            printer.title(
                f"{self.model.unique} is answering to previous response",
                "bold black on yellow",
            )
        self.chat: Chat = self.client.chat.create(**param)
        logger.debug(f"{param=}")

    def attach_role(self):
        role: str = self.data.system_role
        self.chat.append(system(role))

    def attach_prompt(self):

        if self.data.prompt is None:
            raise FileNotFoundError("Load proper prompt first!")

        prompt: str = self.data.prompt
        self.chat.append(user(prompt))

    def attach_images(self):
        for i in self.data.base64_images:
            # LATER: jpeg? worked with png but clarify somewhen
            self.chat.append(
                user(image(image_url=f"data:image/jpeg;base64,{i}"))
            )

    def attach_files(self):
        x = XaiUploader()  # MOVE: do this in data
        if len(self.data.files) > 0:
            if x.compare_with_list(self.data.files):
                logger.success("Files confirmed online")
            else:
                raise FileNotFoundError(
                    "Check uploads, at least 1 file not online!"
                )
        for local_file in self.data.files:  # REMOVE: verification in data
            if local_file.x_id is None:
                logger.warning(f"Ignoring {local_file.name}, no valid x_id!")
            else:
                self.chat.append(user(file(local_file.x_id)))
                logger.debug(
                    f"loaded file: {local_file.topic=}, {local_file.name}, {local_file.x_id}"
                )

    def _get_response(self):
        self.response: Response = self.chat.sample()

    def _extract_full_response(self):
        try:
            self.full_response: str = str(self.response)
        except Exception as e:
            logger.error(f"Error for response: {self.model.api_name}\n{e}")

    def _extract_response_content(self):
        try:
            self.content: str = self.response.content

        except Exception as e:
            logger.error(f"Error for content: {self.model.api_name}\n{e}")

    def _extract_response_id(self):
        self.usage: dict[str, int] = {}
        try:
            usage_from_response = json_format.MessageToDict(
                self.response.usage
            )
            logger.debug(f"{self.model.unique} {usage_from_response=}")

            self.usage = usage_from_response
            printer(self.usage)

        except Exception as e:
            logger.error(f"Usage {self.model.unique}:\n{e}")

    def _calculate_usage_cost(self):
        try:
            self.model.usage_cost(token_usage=self.usage)
            # prints by itself

        except Exception as e:
            logger.error(f"Usage calculcation {self.model.unique}: {e}")

    def _setup_response_data(self):
        try:
            self.data.process_response(
                id=self.response.id,
                model=self.model,
                usage=self.usage,
                content=self.content,
                full_response=self.full_response,
                topic=self.topic,
            )
        except Exception as e:
            logger.error(f"Error for tree {self.model.api_name}\n{e}")
