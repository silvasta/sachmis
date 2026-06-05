from pathlib import Path
from typing import Literal, Self

from boltons.strutils import slugify
from loguru import logger
from pydantic import Field, PrivateAttr

from ...config import SachmisConfig, get_config
from ...exceptions import PromptError
from ..files import Role, SstFile, UploadFile
from .base import ConversationData

config: SachmisConfig = get_config()


class Prompt(ConversationData):
    role: Role | None = None
    files: list[UploadFile] = Field(default_factory=list)
    images: list[SstFile] = Field(default_factory=list)

    partition: Literal["P"] = "P"
    _content: str
    _input_file_path: Path | None = PrivateAttr(default=None)

    @property
    def content(self) -> str:
        return self._content

    @property
    def has_input_file_path(self) -> bool:
        return self._input_file_path is not None

    @property
    def input_file_path(self) -> Path:
        if self._input_file_path is None:
            raise PromptError("Invalid access to path: is None")
        return self._input_file_path

    @property
    def has_role(self) -> bool:
        return self.role is not None

    @property
    def role_content(self) -> str:
        if self.role is None:
            raise PromptError("No Role is loaded!")
        return self.role.content

    @property
    def _spec_for_stem(self) -> str:
        return "prompt"

    @classmethod
    def load_from_path(
        cls,
        local_id: int,
        path: Path | None = None,
        topic: str | None = None,
    ) -> Self:
        """Load new Prompt from Path and generate topic"""

        input_prompt: Path = path or config.paths.input_prompt
        logger.info(f"Loading prompt text from: {input_prompt=}")

        prompt: Self = cls.load_from_text(
            content=input_prompt.read_text(), topic=topic, local_id=local_id
        )
        prompt._input_file_path = input_prompt

        return prompt

    @classmethod
    def load_from_text(
        cls,
        content: str,
        local_id: int,
        topic: str | None = None,
    ) -> Self:
        """Load new Prompt from text and generate topic"""

        logger.info("Preparing Prompt from text input")
        if not content:
            raise PromptError(f"Empty or invalid Prompt! {content=}")
        topic: str = (
            topic or cls.extract_topic(content) or config.defaults.topic
        )
        prompt: Self = cls(
            topic=topic, _content=content, local_id=local_id, partition="P"
        )
        logger.info(f"Prompt loaded with: {topic=}")

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

        raise PromptError(f"Can't extract prompt topic! {prompt_text=}")
