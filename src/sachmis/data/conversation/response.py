from pathlib import Path
from typing import Self

from loguru import logger
from pydantic import Field

from sachmis.exceptions import SachmisError

from .base import Conversation


class ResponseData(Conversation):
    model: str
    remote_id: str

    usage: dict = Field(default_factory=dict)
    full_response: Path

    @property
    def _spec_for_stem(self) -> str:
        return self.model

    @classmethod
    def from_model(
        cls,
        content: str,
        model: str,
        remote_id: str,
        usage: dict,
        full_response: Path,
        topic: str,
    ) -> Self:
        logger.debug(f"Processing Response for {model}: {topic}")
        if remote_id:
            logger.info(f"found response id: {remote_id}")
        return cls(
            content=content,
            model=model,
            remote_id=remote_id,
            usage=usage,
            full_response=full_response,
            topic=topic,
        )


class Response(ResponseData):
    grandfather_uid: str | None  # unique_id of prompt with multiple ancestors
    ancestor: Conversation
    successor: list[Conversation] = Field(default_factory=list)

    def _get_ancestor(self) -> Conversation:
        return self.ancestor

    def _get_successor(self) -> list[Conversation]:
        return self.successor

    @classmethod
    def upgrade_from_raw(
        cls,
        raw_response: ResponseData,
        ancestor: Conversation,
        local_id: int,
    ) -> Self:
        logger.info(f"Upgrading raw_response: {local_id=}, {ancestor=}")

        try:
            grandfather: Conversation | None = ancestor.get_ancestor()
            assert isinstance(grandfather, Response)
            grandfather_id: str = grandfather.unique_id

        except SachmisError as error:
            logger.error(f"Problem while finding fathers: {error=}")
            grandfather_id: str | None = None

        response: Self = cls(
            local_id=local_id,
            grandfather_uid=grandfather_id,
            ancestor=ancestor,
            **raw_response.model_dump(),
        )

        logger.success(f"Upgraded to Response with: {response.stem=}")

        return response
