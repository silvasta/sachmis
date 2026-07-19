import uuid
from dataclasses import dataclass
from typing import Self

from ..config.models import ModelFamily
from .conversation.prompt import Prompt


@dataclass
class SproutSelectorDTO:  # TASK: rename, review
    """
    Provide scanned Data in displayable form until Selection of Models
    - Data will be absorbed by SelectedConversation
    """

    selector_uuid: str
    selector_display_name: str
    model: ModelFamily
    tree_id: int = 0
    sprout_id: int = 0

    @classmethod
    def from_file(cls, model: ModelFamily, tree_id, sprout_id) -> Self:
        return cls(
            selector_uuid=str(uuid.uuid4()),
            selector_display_name=model.id_cli,
            model=model,
            tree_id=tree_id,
            sprout_id=sprout_id,
        )


@dataclass
class SelectedSproutDTO:  # TASK: rename, review
    """
    Provide selected Data in condensed form until Init of Models
    - Replaces SproutSelectorDTO after Selection
    - Data will be absorbed by ConversationNode
    """

    model: ModelFamily
    tree_id: int = 0
    sprout_id: int = 0

    @classmethod
    def from_scan(cls, selected: SproutSelectorDTO) -> Self:
        return cls(
            model=selected.model,
            tree_id=selected.tree_id,
            sprout_id=selected.sprout_id,
        )

    @classmethod
    def from_zero(cls, fresh_models: list[ModelFamily]) -> list[Self]:
        return [
            cls(model=model, tree_id=0, sprout_id=0) for model in fresh_models
        ]


@dataclass
class SproutPackage:  # TODO: DTO?
    model: ModelFamily
    prompt: Prompt
    next_response_id: str
    previous_response_id: str | None
    previous_remote_id: str | None
