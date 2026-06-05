from pathlib import Path
from typing import Literal

from pydantic import Field

from .base import ConversationData


class Response(ConversationData):
    model: str
    remote_id: str

    _content: str

    partition: Literal["R"] = "R"

    usage: dict = Field(default_factory=dict)
    full_response: Path

    @property
    def content(self) -> str:
        return self._content

    @property
    def _spec_for_stem(self) -> str:
        return self.model
