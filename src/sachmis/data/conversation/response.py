from pathlib import Path
from typing import Literal

from pydantic import Field

from ...config import SachmisConfig, get_config
from .base import ConversationData

config: SachmisConfig = get_config()


class Response(ConversationData):
    partition: Literal["R"] = "R"

    model: str
    remote_id: str

    usage: dict = Field(default_factory=dict)
    full_response: Path

    def _prepare_text_from_content(self):
        return self.content

    def _assemble_stem(self) -> str:
        return config.names.response_stem(
            id=self.sprout_id, model=self.model, topic=self.topic
        )
