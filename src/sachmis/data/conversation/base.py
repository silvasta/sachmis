"""
Provide shared attributes and namespace for Prompt and Response

- Handle id and basic file system management

"""

__all__: list[str] = [
    "Conversation",
]

import uuid
from typing import Any

from boltons.strutils import slugify
from pydantic import BaseModel, Field, model_validator


class Conversation(BaseModel):
    """Prepare Base for all Prompts and Responses"""

    unique_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    tree_id: int = Field(ge=1)
    sprout_id: int = Field(ge=1)
    topic: str

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

    # TODO: View

    def __str__(self):
        return f"{type(self).__name__}_{self.sprout_id} with {self.topic=}"

    @classmethod
    @model_validator(mode="before")
    def slugify_topic_save_both_use_slug_as_topic(cls, data: Any) -> Any:
        if isinstance(data, dict) and "topic" in data:
            data["no_slug_topic"] = data.get("no_slug_topic", data["topic"])
            data["topic"] = slugify(str(data["topic"]))
        return data
