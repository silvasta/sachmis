from google.genai import Client, types
from google.genai.types import GenerateContentResponse
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from sachmis.config.manager import config
from sachmis.config.model import Geminis
from sachmis.data import DataManager
from sachmis.utils.print import printer

from .agent import Model

# NEXT: adapt function names! _xxx()


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

        # TODO: gemini default config to config.defaults
        self.thinking_budget: int | None = thinking_budget

        # INFO: super() after storing variables for:
        # - self._load_client()
        # - data.attach()
        super().__init__(data, model, topic)

    def _load_client(self):
        self.client = Client(
            api_key=config.from_env(key="GEMINI_API_KEY"),
        )

    def prepare_chat(self):
        self.contents: list = []  # INFO: this is where all files,images, role and prompt get collected
        self.content_config: dict = {}
        if self.thinking_budget:
            self.content_config |= {
                "thinking_config": types.ThinkingConfig(
                    thinking_budget=self.thinking_budget
                ),
            }
        # FIX:
        # if self.previous_response_id:
        #     logger.info(
        #         "Answer to Gemini here but, prepare file structure first!"
        #     )

    def attach_role(self):
        role: str = self.data.system_role
        self.content_config |= {"system_instruction": role}

    def attach_prompt(self):

        if self.data.prompt is None:
            raise FileNotFoundError("Load proper prompt first!")

        prompt: str = self.data.prompt
        self.contents.append(prompt)

    def attach_images(self):
        for i in self.data.bytes_images:
            mime: str = (
                "image/png" if i.startswith(b"\x89PNG") else "image/jpeg"
            )
            self.contents.append(
                types.Part.from_bytes(data=i, mime_type=mime),
            )

    def attach_files(self):
        for local_file in self.data.files:
            if local_file.g_uri is None:  # REMOVE: verification in data
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

    @retry(
        stop=stop_after_attempt(config.defaults.tenacity.max_attempts),
        wait=wait_exponential(**config.defaults.tenacity.wait_exponential),
        # TODO: before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def _get_response(self):
        self.response: GenerateContentResponse = (
            self.client.models.generate_content(
                model=self.model.api_name,
                contents=self.contents,
                config=types.GenerateContentConfig(**self.content_config),
            )
        )

    def _extract_full_response(self):
        try:
            self.full_response: str = str(self.response)
        except Exception as e:
            logger.error(f"Error for content: {self.model.api_name}\n{e}")

    def _extract_response_content(self):
        try:
            self.content: str = self.response.text or ""
        except Exception as e:
            logger.error(f"Error for content: {self.model.api_name}\n{e}")

    def _extract_response_id(self):
        if self.response.response_id is None:
            logger.error(f"Fail for response_id! {self.model=}")
            self.id = "FAIL"
        else:
            self.id: str = self.response.response_id

    def _extract_usage(self):
        self.usage: dict[str, int] = {}
        try:
            if self.response.usage_metadata is None:
                logger.error(f"Fail with usage_metadata! {self.model=}")
            else:
                usage_from_response = self.response.usage_metadata
                logger.debug(f"{self.model.unique} {usage_from_response=}")

            # TODO: improve this!
            self.usage = usage_from_response
            printer(self.usage)

        except Exception as e:
            logger.error(f"Usage {self.model.unique}:\n{e}")

    def _calculate_usage_cost(self):
        printer("Implement usage calculation for Gemini!")

    def _setup_response_data(self):
        try:
            self.data.process_response(
                id=self.id,
                model=self.model,
                usage=self.usage,
                content=self.content,
                full_response=self.full_response,
                topic=self.topic,
            )
        except Exception as e:
            logger.error(f"Error for tree {self.model.api_name}\n{e}")
