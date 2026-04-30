from google.genai import Client, types
from google.genai.types import GenerateContentResponse
from loguru import logger

# from tenacity import retry, stop_after_attempt, wait_exponential
from ...config import SachmisConfig, get_config
from ...config.defaults import GeminiParam
from ...config.model import Geminis
from ...utils.print import printer
from .agent import Model

config: SachmisConfig = get_config()


class Gemini(Model):
    model: Geminis
    param: GeminiParam
    client: Client
    response: GenerateContentResponse

    def _load_client(self):
        self.client = Client(
            api_key=config.from_env(key="GEMINI_API_KEY"),
        )

    def prepare_chat(self):
        self.contents: list = []  # INFO: this is where all files,images, role and prompt get collected
        self.content_config: dict = {}
        if self.param.thinking_budget:
            self.content_config |= {
                "thinking_config": types.ThinkingConfig(
                    thinking_budget=self.param.thinking_budget
                ),
            }
        # TASK:
        # if self.previous_response_id:
        #     logger.info(
        #         "Answer to Gemini here but, prepare file structure first!"
        #     )

    def _attach_role(self, role: str):
        self.content_config |= {"system_instruction": role}

    def _attach_prompt(self, prompt: str):
        self.contents.append(prompt)

    def attach_images(self):
        for i in self.data._images:
            # FIX: image
            # mime: str = (
            #     "image/png" if i.startswith(b"\x89PNG") else "image/jpeg"
            # )
            # self.contents.append(
            #     types.Part.from_bytes(data=i, mime_type=mime),
            # )
            # TODO: images loading
            # def load_input_image(self, image_path: Path) -> None:
            #     """So far, encoding image to base64 string"""
            #
            #     # bytes image loading for gemini
            #     if image := load_bytes_image(image_path):
            #         self.bytes_images.append(image)
            #     else:
            #         logger.warning(f"Bytes image loading failed: {image_path}")
            #     self.input_image_paths.append(image_path)
            logger.debug(f"ignoring {i}")

    def attach_files(self):
        # for local_file in self.data.files:
        #     if local_file.g_uri is None:  # REMOVE: verification in data
        #         logger.warning(f"Ignoring {local_file.name}, no valid g_id!")
        #     else:
        #         logger.debug(
        #             f"loaded file: {local_file.topic=}, {local_file.name}, {local_file.g_uri}"
        #         )
        #         self.contents.append(
        #             types.Part.from_uri(
        #                 file_uri=local_file.g_uri,
        #                 mime_type=local_file.g_mime_type,
        #             )
        #         )
        pass

    # @retry( # IMPORTANT: retry
    #     stop=stop_after_attempt(config.defaults.tenacity.max_attempts),
    #     wait=wait_exponential(**config.defaults.tenacity.wait_exponential),
    #     # TODO: before_sleep=before_sleep_log(logger, logging.WARNING)
    # )
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

    def _calculate_usage_cost(self, usage: dict):
        printer("Implement usage calculation for Gemini!")
        printer(usage)
