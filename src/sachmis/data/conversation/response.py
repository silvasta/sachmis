from pathlib import Path
from typing import Self

from loguru import logger
from pydantic import Field

from .base import ConversationData


class Response(ConversationData):
    model: str
    remote_id: str

    _content: str

    usage: dict = Field(default_factory=dict)
    full_response: Path

    @property
    def content(self) -> str:
        return self._content

    @property
    def _spec_for_stem(self) -> str:
        return self.model

    @classmethod
    def from_model(  # REMOVE: ???
        cls,
        content: str,
        model: str,
        remote_id: str,
        local_id: int,
        usage: dict,
        full_response: Path,
        topic: str,
    ) -> Self:
        logger.debug(f"Processing Response for {model}: {topic}")
        if remote_id:
            logger.info(f"found response id: {remote_id}")
        return cls(
            _content=content,
            model=model,
            remote_id=remote_id,
            usage=usage,
            full_response=full_response,
            topic=topic,
            local_id=local_id,
            partition="R",
        )
