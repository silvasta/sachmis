from pathlib import Path

from pydantic import Field

from ...config import SachmisConfig, get_config
from ..files import Conversation


class Response(Conversation):
    model: str
    remote_id: str

    usage: dict = Field(default_factory=dict)
    full_response: Path

    ancestor: Conversation
    successor: list[Conversation] = Field(default_factory=list)

    def _get_ancestor(self) -> Conversation:
        return self.ancestor

    def _get_successor(self) -> list[Conversation]:
        return self.successor

    def _compose_stem(self) -> str:
        config: SachmisConfig = get_config()
        return config.names.sprout_stem.computed(
            locator=f"{self.local_id}", spec=self.model, topic=self.topic
        )

    def rollout_path(self, root_dir: Path | None = None) -> Path:
        config: SachmisConfig = get_config()
        return config.paths.answer_file(
            answer_stem=self._compose_stem(), root_dir=root_dir
        )

    def single_ancestor(self) -> Conversation:
        return self._get_ancestor()
