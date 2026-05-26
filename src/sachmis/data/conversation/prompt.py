from pathlib import Path
from typing import Self

from boltons.strutils import slugify
from loguru import logger
from pydantic import Field, PrivateAttr

from ...config import SachmisConfig, get_config
from ...exceptions import PromptError
from ...exceptions.data import PromptRegistryError
from ..files import Role, SstFile, UploadFile
from .base import Conversation

config: SachmisConfig = get_config()


class PromptData(Conversation):
    role: Role | None = None
    files: list[UploadFile] = Field(default_factory=list)
    images: list[SstFile] = Field(default_factory=list)

    _input_file_path: Path | None = PrivateAttr(default=None)

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
        cls, path: Path | None = None, topic: str | None = None
    ) -> Self:
        """Load new Prompt from Path and generate topic"""

        input_prompt: Path = path or config.paths.input_prompt
        logger.info(f"Loading prompt text from: {input_prompt=}")

        prompt: Self = cls.load_from_text(
            content=input_prompt.read_text(), topic=topic
        )
        prompt._input_file_path: Path = input_prompt

        return prompt

    @classmethod
    def load_from_text(
        cls,
        content: str,
        topic: str | None = None,
    ) -> Self:
        """Load new Prompt from text and generate topic"""

        logger.info("Preparing Prompt from text input")
        if not content:
            raise PromptError(f"Empty or invalid Prompt! {content=}")
        topic: str = (
            topic or cls.extract_topic(content) or config.defaults.topic
        )
        prompt: Self = cls(topic=topic, content=content)
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


class Prompt(PromptData):
    # IDEA: use just unique_id for predecessor?
    # IDEA: Response grandfather as new prompt type?
    ancestor: Conversation | tuple[Conversation] | None
    successor: list[Conversation] = Field(default_factory=list)

    def _get_ancestor(self) -> Conversation | tuple[Conversation] | None:
        return self.ancestor

    def _get_successor(self) -> list[Conversation]:
        if not self.successor:
            raise PromptRegistryError("Prompt must have at least 1 successor")
        return self.successor

    def single_ancestor(self) -> Conversation:
        if not isinstance(ancestor := self.ancestor, Conversation):
            raise PromptRegistryError
        self._ensure_class_swiched(ancestor)
        return ancestor

    def multi_ancestor(self) -> tuple[Conversation]:
        if not isinstance(ancestors := self.ancestor, tuple):
            raise PromptRegistryError
        for ancestor in ancestors:
            self._ensure_class_swiched(ancestor)
        return ancestors

    @property
    def is_root_prompt(self):
        return self.n_ancestor == 0

    @property
    def n_ancestor(self) -> int:
        if (ancestor := self.ancestor) is None:
            return 0
        if not isinstance(ancestor, tuple):
            return 1
        return len(ancestor)

    @classmethod
    def upgrade_from_raw(
        cls,
        raw_prompt: PromptData,
        ancestor: Conversation | tuple[Conversation] | None,
        local_id: int,
    ) -> Self:
        logger.info(f"Upgrading raw_prompt: {local_id=}, {ancestor=}")
        prompt: Self = cls(
            local_id=local_id,
            ancestor=ancestor,
            **raw_prompt.model_dump(),
        )
        match n_ancestor := prompt.n_ancestor:
            case 0:
                logger.info(f"Created new Prompt as root_prompt {n_ancestor=}")
            case 1:  # TODO: confirm
                logger.info(f"Created Prompt with {n_ancestor=}")
            case _:  # TODO: confirm
                logger.info(f"Created Prompt with {n_ancestor=}")

        logger.success(f"Upgraded to Promt with: {prompt.stem=}")

        return prompt
