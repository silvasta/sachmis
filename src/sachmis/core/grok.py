from google.protobuf import json_format
from .uploader import XaiUploader
from loguru import logger
from xai_sdk import Client
from xai_sdk.chat import Response, image, system, user, file
from xai_sdk.sync.chat import Chat

from ..utils.print import printer
from .model import Model
from .data import DataManager
from .models import Groks


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
            api_key=self.data.config.from_env(key="XAI_API_KEY"),
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
            # TODO: raise at load_prompt or send message from here
            raise FileNotFoundError("Load proper prompt first!")
        prompt: str = self.data.prompt
        self.chat.append(user(prompt))

    def attach_images(self):
        for i in self.data.base64_images:
            # NOTE: jpeg? worked with png but clarify somewhen
            self.chat.append(user(image(image_url=f"data:image/jpeg;base64,{i}")))

    def attach_files(self):
        x = XaiUploader()
        if len(self.data.files) > 0:
            if x.compare_with_list(self.data.files):
                logger.success("Files confirmed online")
            else:
                raise FileNotFoundError("Check uploads, at least 1 file not online!")
        for local_file in self.data.files:
            if local_file.x_id is None:
                logger.warning(f"Ignoring {local_file.name}, no valid x_id!")
            else:
                self.chat.append(user(file(local_file.x_id)))
                logger.debug(
                    f"loaded file: {local_file.topic=}, {local_file.name}, {local_file.x_id}"
                )

    def fire(self):
        """Assemble prompt and release"""

        logger.info("Fire")
        self.response: Response = self.chat.sample()

        logger.info("Got response, start processing...")
        self.process_response()

    def process_response(self):
        try:
            full_response: str = str(self.response)

            printer.title(f"Response Content ({self.model.unique})", style="write")
            content: str = self.response.content
            printer.md(content)
        except Exception as e:
            logger.error(f"Error for content: {self.model.api_name}\n{e}")

        usage: dict[str, int] = {}
        try:
            usage_response = json_format.MessageToDict(self.response.usage)
            logger.debug(f"{self.model.unique} {usage_response=}")
            printer.print(usage_response)
            for key, value in usage_response.items():
                if isinstance(value, int):
                    usage[key] = value
                else:
                    logger.warning(f"Ignoring for usage: ({key=}, {value=})")
        except Exception as e:
            logger.error(f"Usage {self.model.unique}: {e}")
        try:
            # usage calculation (still bugs... and not so important to let usage crash)
            self.model.usage_cost(token_usage=usage)  # prints by itself
        except Exception as e:
            logger.error(f"Usage calculcation {self.model.unique}: {e}")

        try:
            self.data.process_response(
                id=self.response.id,
                model=self.model,
                usage=usage,
                content=content,
                full_response=full_response,
                topic=self.topic,
            )
        except Exception as e:
            logger.error(f"Error for tree {self.model.api_name}\n{e}")
            # WARN: write here content, etc directly?
        logger.info(f"End of {self.model}")
