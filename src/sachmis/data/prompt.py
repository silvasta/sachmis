from pathlib import Path
from typing import Self

from boltons.strutils import slugify
from loguru import logger
from pydantic import BaseModel, Field

from ..config import SachmisConfig, get_config
from ..exceptions import PromptError
from .files import SstFile, UploadFile


class Prompt(BaseModel):
    topic: str
    text: str
    files: list[UploadFile] = Field(default_factory=list)
    images: list[SstFile] = Field(default_factory=list)
    # TODO: role as something like Role(SstFile)

    @property
    def slug_topic(self):
        return slugify(self.topic)

    def get_path(self, root_dir: Path | None = None) -> Path:
        config: SachmisConfig = get_config()
        return config.paths.prompt_file(
            topic=self.slug_topic,
            root_dir=root_dir,  # PARAM: nested!
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
        prompt: Prompt = cls(topic=topic, text=prompt_text)
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
