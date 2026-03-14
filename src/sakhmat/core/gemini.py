from google.genai import Client, types
from google.genai.types import GenerateContentResponse
from loguru import logger

from ..utils.print import printer
from .model import Model
from .data import DataManager
from .models import Geminis


class Gemini(Model):
    model: Geminis
    client: Client
    response: GenerateContentResponse

    def __init__(
        self,
        data: DataManager,
        model: Geminis,
        topic: str | None = None,
        thinking_budget: int | None = -1,  # -1 = dynamic, 0 = off, 1024 = high
    ):
        super().__init__(data, model, topic)

        self.thinking_budget = thinking_budget

        self._boot()

    def load_client(self):
        self.client = Client(api_key=self.data.config.from_env(key="GEMINI_API_KEY"))
        logger.debug("Client loaded")

    def prepare_chat(self):
        self.contents: list = []  # INFO: this is where all files,images, role and prompt get collected
        self.content_config: dict = {}
        if self.thinking_budget:
            self.content_config |= {
                "thinking_config": types.ThinkingConfig(
                    thinking_budget=self.thinking_budget
                ),
            }
        if self.previous_response_id:
            logger.info("Answer to Gemini here but, prepare file structure first!")

    def attach_role(self):
        role: str = self.data.system_role
        self.content_config |= {"system_instruction": role}

    def attach_prompt(self):
        if self.data.prompt is None:
            # TODO: raise at load_prompt or send message from here
            raise FileNotFoundError("Load proper prompt first!")
        prompt: str = self.data.prompt
        self.contents.append(prompt)

    def attach_images(self):
        for i in self.data.bytes_images:
            mime: str = "image/png" if i.startswith(b"\x89PNG") else "image/jpeg"
            self.contents.append(
                types.Part.from_bytes(data=i, mime_type=mime),
            )

    def attach_files(self):
        for local_file in self.data.files:
            if local_file.g_uri is None:
                logger.warning(f"Ignoring {local_file.name}, no valid g_id!")
            else:
                logger.debug(
                    f"loaded file: {local_file.topic=}, {local_file.name}, {local_file.g_uri}"
                )
                self.contents.append(
                    types.Part.from_uri(
                        file_uri=local_file.g_uri,
                        mime_type=local_file.g_mime_type,
                    )
                )

    def fire(self):
        """Assemble prompt and release"""

        logger.info("Fire")
        self.response: GenerateContentResponse = self.client.models.generate_content(
            model=self.model.api_name,
            contents=self.contents,
            config=types.GenerateContentConfig(**self.content_config),
        )
        logger.info("Got response, start processing...")
        self.process_response()

    def process_response(self):
        try:
            full_response: str = str(self.response)

            printer.title(f"Response Content ({self.model.unique})", style="write")
            content: str = self.response.text or ""
            printer.md(content)
        except Exception as e:
            logger.error(f"Error for content: {self.model.api_name}\n{e}")

        if self.response.response_id is None:
            logger.error(f"Fail with response_id! {self.model=}")
            id = "FAIL"
        else:
            id: str = self.response.response_id

        usage: dict[str, int] = {}
        try:
            if self.response.usage_metadata is None:
                logger.error(f"Fail with usage_metadata! {self.model=}")
            else:
                for key, value in self.response.usage_metadata:
                    if isinstance(value, int):
                        usage[key] = value
                    else:
                        logger.warning(f"Ignoring for usage: ({key=}, {value=})")

            #      NOTE: form response := {
            #     'candidates_token_count': 64,
            #     'prompt_token_count': 35,
            #     'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 35}],
            #     'thoughts_token_count': 501,
            #     'total_token_count': 600 }

        except Exception as e:
            logger.error(f"Error for usage: {self.model.api_name}\n{e}")

            printer.print(usage)

        try:
            self.data.process_response(
                id=id,
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
