import uuid
from typing import Any, Literal

from boltons.strutils import slugify
from pydantic import BaseModel, Field, model_validator

from ...config import SachmisConfig, get_config

config: SachmisConfig = get_config()

# LATER:
# from sstcore.utils import SimpleTreeNode
# class SproutNode(SimpleTreeNode):
#     """This maybe as snapshot of DAG, for CLI and TUI"""


class ConversationData(BaseModel):
    """Prepare Base for all Prompts and Responses"""

    partition: Literal["P", "R"]
    unique_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    sprout_id: int = Field(ge=1)

    topic: str
    content: str  # LATER: other data types

    no_slug_topic: str | None = None  # Saves the original un-slugified topic

    def _prepare_text_from_content(self):
        raise NotImplementedError

    def _assemble_stem(self) -> str:
        raise NotImplementedError

    @property
    def text(self) -> str:
        """Convert content to result for rendering"""
        return self._prepare_text_from_content()

    @property
    def sprout_stem(self) -> str:
        return self._assemble_stem()

    def __repr__(self):  # TASK: this for all major classes
        return f"{self.__class__.__name__}(sprout_id={self.sprout_id})"

    def __str__(self):  # TASK: this for all major classes
        return f"{self.__class__.__name__}_{self.sprout_id} with {self.topic=}"

    @classmethod
    @model_validator(mode="before")
    def slugify_topic_save_both_use_slug_as_topic(cls, data: Any) -> Any:
        if isinstance(data, dict) and "topic" in data:
            data["no_slug_topic"] = data.get("no_slug_topic", data["topic"])
            data["topic"] = slugify(str(data["topic"]))
        return data
