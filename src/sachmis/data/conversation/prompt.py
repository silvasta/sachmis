from typing import Literal, Self

from boltons.strutils import slugify
from loguru import logger
from pydantic import Field
from sstcore.data import SstFile

from ...config import SachmisConfig, get_config
from ...exceptions import PromptError
from ..files import Role, UploadFile
from .base import ConversationData

config: SachmisConfig = get_config()


class Prompt(ConversationData):
    partition: Literal["P"] = "P"

    role: Role | None = None  # LATER: replace by layout
    files: list[UploadFile] = Field(default_factory=list)
    images: list[SstFile] = Field(default_factory=list)

    content: str

    def attach_role(self, role: Role | None):
        self.role: Role | None = role
        logger.info(f"Attached Role: {self.role}")

    def attach_files(self, files: list[UploadFile]):
        self.files: list[UploadFile] = files
        logger.info(f"Attached Files: {len(self.files)}")

    def attach_images(self, images: list[SstFile]):
        self.images: list[SstFile] = images
        logger.info(f"Attached Images: {len(self.images)}")

    @classmethod
    def from_text(
        cls, content: str, sprout_id: int, topic: str | None = None
    ) -> Self:
        """Load new Prompt from text and generate topic"""

        logger.info("Preparing Prompt from text input")

        if not content:
            raise PromptError(f"Empty or invalid Prompt! {content=}")

        topic: str = cls._find_topic(topic=topic, content=content)

        prompt: Self = cls(topic=topic, content=content, sprout_id=sprout_id)
        logger.info(f"Loaded: {prompt}")

        return prompt

    @property
    def has_role(self) -> bool:
        return self.role is not None

    @property
    def role_content(self) -> str:
        if self.role is None:
            raise PromptError("No Role is loaded!")
        return self.role.content

    def _prepare_text_from_content(self):
        return self.content

    def _assemble_stem(self) -> str:
        return config.names.prompt_stem(id=self.sprout_id, topic=self.topic)

    @staticmethod
    def _find_topic(topic: str | None, content: str) -> str:
        if topic:
            return topic
        if topic := Prompt.extract_topic(content):
            return topic
        return config.defaults.topic

    @staticmethod
    def extract_topic(prompt_text: str) -> str:
        """Find first line with content and create slug"""

        if lines := prompt_text.splitlines():
            first_non_empty_line: str | None = next(
                (line.strip() for line in lines if line.strip()), None
            )
            if first_non_empty_line:
                topic: str = slugify(first_non_empty_line, delim="-")
                return topic

        raise PromptError(f"Can't extract topic! {prompt_text=}")
