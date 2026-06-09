from typing import Literal, Self

from boltons.strutils import slugify
from loguru import logger
from pydantic import Field

from ...config import SachmisConfig, get_config
from ...exceptions import PromptError
from ..files import Role, SstFile, UploadFile
from .base import ConversationData

config: SachmisConfig = get_config()


class Prompt(ConversationData):
    partition: Literal["P"] = "P"

    role: Role | None = None  # LATER: replace by layout
    files: list[UploadFile] = Field(default_factory=list)
    images: list[SstFile] = Field(default_factory=list)

    content: str

    @classmethod
    def from_text(
        cls, content: str, sprout_id: int, topic: str | None = None
    ) -> Self:
        """Load new Prompt from text and generate topic"""

        logger.info("Preparing Prompt from text input")
        if not content:
            raise PromptError(f"Empty or invalid Prompt! {content=}")
        topic: str = (
            topic or cls.extract_topic(content) or config.defaults.topic
        )
        prompt: Self = cls(topic=topic, content=content, sprout_id=sprout_id)
        logger.info(f"Loaded: {prompt}")

        return prompt

    @staticmethod
    def extract_topic(prompt_text: str) -> str:

        if lines := prompt_text.splitlines():
            first_non_empty_line: str | None = next(
                (line.strip() for line in lines if line.strip()), None
            )
            if first_non_empty_line:
                topic: str = slugify(first_non_empty_line, delim="-")
                return topic

        raise PromptError(f"Can't extract topic! {prompt_text=}")

    # NEXT:
    @property  # TODO: check
    def has_role(self) -> bool:
        return self.role is not None

    # NEXT:
    @property  # TODO: check
    def role_content(self) -> str:
        if self.role is None:
            raise PromptError("No Role is loaded!")
        return self.role.content

    def _prepare_text_from_content(self):
        return self.content

    def _assemble_stem(self) -> str:
        return config.names.prompt_stem(id=self.sprout_id, topic=self.topic)
