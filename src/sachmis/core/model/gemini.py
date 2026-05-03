from google.genai import Client, types
from google.genai.types import GenerateContentResponse
from loguru import logger

from sachmis.data.files import GoogleUploadState
from sachmis.exceptions import SachmisDataError

# from tenacity import retry, stop_after_attempt, wait_exponential
from ...config import SachmisConfig, get_config
from ...config.defaults import GeminiParam, ModelParam
from ...config.model import Geminis
from ...utils.print import printer
from .agent import Model

config: SachmisConfig = get_config()


class Gemini(Model):
    model: Geminis
    param: GeminiParam
    client: Client
    _raw_response: GenerateContentResponse

    def _load_param(self, param: ModelParam | None) -> GeminiParam:
        """Load defaults if param not set"""

        if param is None:
            config: SachmisConfig = get_config()
            param: GeminiParam = config.defaults.gemini

        if isinstance(param, GeminiParam):
            return param

        raise SachmisDataError(f"{self.__class__.__name__}: Invalid {param=}")

    def _load_client(self):
        self.client = Client(
            api_key=config.from_env(key="GEMINI_API_KEY"),
        )

    def _prepare_chat(self):
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

    def _attach_images(self):
        for i in self.prompt.images:
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

    def _attach_files(self):
        for upload_file in self.prompt.files:
            state = upload_file.get_remote_state(self.model.target)
            if isinstance(state, GoogleUploadState):
                self.contents.append(
                    types.Part.from_uri(
                        file_uri=state.g_uri,
                        mime_type=state.g_mime_type,
                    )
                )
                logger.debug(f"loaded: {upload_file.name=}, {state.g_uri}")
            else:
                logger.warning(f"Failed: {upload_file=}")

    # @retry( # LATER: retry
    #     stop=stop_after_attempt(config.defaults.tenacity.max_attempts),
    #     wait=wait_exponential(**config.defaults.tenacity.wait_exponential),
    #     # TODO: before_sleep=before_sleep_log(logger, logging.WARNING)
    # )
    def _get_response(self):
        response: GenerateContentResponse = (
            self.client.models.generate_content(
                model=self.model.api_name,
                contents=self.contents,
                config=types.GenerateContentConfig(**self.content_config),
            )
        )
        return response

    def _extract_full_response(self) -> str:
        try:
            return str(self._raw_response)
        except Exception as e:
            logger.error(f"Error for response: {self.model.api_name}\n{e}")
            raise

    def _extract_response_content(self) -> str:
        try:
            return self._raw_response.text or ""
        except Exception as e:
            logger.error(f"Error for content: {self.model.api_name}\n{e}")
            raise

    def _extract_response_id(self) -> str:
        try:
            return self._raw_response.response_id or "FAIL"
        except Exception as e:
            logger.error(f"Error for ID: {self.model.api_name}\n{e}")
            return "FAIL"

    def _extract_usage(self) -> dict | None:
        try:
            if self._raw_response.usage_metadata is None:
                logger.error(f"Fail with usage_metadata! {self.model=}")
            else:
                return self._raw_response.usage_metadata.model_dump()
        except Exception as e:
            logger.error(f"Usage {self.model.unique}:\n{e}")

    def _calculate_usage_cost(self, usage: dict) -> bool:
        printer("NotImplemented! Usage calculation for Gemini")
        return False
