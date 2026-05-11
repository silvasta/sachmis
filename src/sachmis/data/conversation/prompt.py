from pathlib import Path
from typing import Self

from boltons.strutils import slugify
from loguru import logger
from pydantic import Field

from ...config import SachmisConfig, get_config
from ...exceptions import PromptError
from ..files import Conversation, ConversationTreeNode, SstFile, UploadFile


class PromptTreeNode(ConversationTreeNode):
    pass


class Prompt(Conversation):
    files: list[UploadFile] = Field(default_factory=list)
    images: list[SstFile] = Field(default_factory=list)
    # TODO: role as something like Role(SstFile)

    ancestor: Conversation | tuple[Conversation] | None = None
    # TODO: len(successor) > 0
    successor: list[Conversation] = Field(default_factory=list)

    def _get_ancestor(self) -> Conversation | tuple[Conversation] | None:
        return self.ancestor

    def n_ancestor(self) -> int:
        if (ancestor := self.ancestor) is None:
            return 0
        if not isinstance(ancestor, tuple):
            return 1
        return len(ancestor)

    def single_ancestor(self) -> Conversation | None:
        if isinstance(self.ancestor, tuple):
            return None
        return self.ancestor

    def _get_successor(self) -> list[Conversation]:
        if not self.successor:
            raise PromptError("Prompt must have at least 1 successor")
        return self.successor

    def _compose_stem(self) -> str:
        config: SachmisConfig = get_config()
        return config.names.sprout_stem.computed(
            locator=f"{self.local_id}",
            spec="prompt",
            topic=self.slug_topic,
        )

    def rollout_path(self, root_dir: Path | None = None) -> Path:
        config: SachmisConfig = get_config()
        return config.paths.prompt_file(
            prompt_stem=self._compose_stem(), root_dir=root_dir
        )

    @classmethod
    def load_from_path(
        cls, path: Path | None = None, topic: str | None = None
    ) -> Self:
        """Load new Prompt from Path and generate topic"""
        config: SachmisConfig = get_config()

        path: Path = path or Path(config.names.prompt)
        logger.info(f"Loading prompt text from: {path=}")

        return cls.load_from_text(prompt_text=path.read_text(), topic=topic)

    @classmethod
    def load_from_text(
        cls, prompt_text: str, topic: str | None = None
    ) -> Self:
        """Load new Prompt from text and generate topic"""
        config: SachmisConfig = get_config()

        logger.info("Preparing Prompt from text input")

        if not prompt_text:
            raise PromptError(f"Empty or invalid Prompt! {prompt_text=}")

        topic: str = (
            topic or cls.extract_topic(prompt_text) or config.defaults.topic
        )
        prompt: Prompt = cls(
            topic=topic,
            content=prompt_text,
            local_id=-1,
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
