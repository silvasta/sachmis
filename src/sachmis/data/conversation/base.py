import uuid
from pathlib import Path
from typing import Any, Literal

from boltons.strutils import slugify
from loguru import logger
from pydantic import BaseModel, Field, model_validator

from ...config import SachmisConfig, get_config

config: SachmisConfig = get_config()

# LATER:
# from sstcore.utils import SimpleTreeNode
# class SproutNode(SimpleTreeNode):
#     """This maybe as snapshot of DAG, for CLI and TUI"""


class ConversationData(BaseModel):
    """Beginning of all Prompts and Conversations"""

    unique_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    partition: Literal["P", "R"]

    local_id: int = Field(ge=1)
    topic: str

    original_topic: str | None = None  # Saves the original un-slugified topic

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.local_id})"

    def __str__(self):
        return f"{self.__class__.__name__}_{self.local_id} with {self.topic=}"

    @property
    def stem(self) -> str:
        return self._compose_stem()

    @property
    def _spec_for_stem(self) -> str:
        raise NotImplementedError

    @property
    def content(self) -> str:
        raise NotImplementedError

    def write(self, root_dir: Path | None = None) -> Path:
        """Rollout to FileSystem"""
        path: Path = self.rollout_path(root_dir)
        path.write_text(self.content)
        logger.info(f"{self.__class__.__name__} written to: {path=}")
        return path

    def rollout_path(self, root_dir: Path | None = None) -> Path:
        return config.paths.conversation_file(
            stem=self._compose_stem(), root_dir=root_dir
        )

    def _compose_stem(self) -> str:
        return config.names.sprout_stem.computed(
            locator=f"{self.local_id}",
            spec=self._spec_for_stem,
            topic=self.topic,
        )

    @classmethod
    @model_validator(mode="before")
    def slugify_topic_save_both_use_slug_as_topic(cls, data: Any) -> Any:
        if isinstance(data, dict) and "topic" in data:
            data["original_topic"] = data.get("original_topic", data["topic"])
            data["topic"] = slugify(str(data["topic"]))
        return data
