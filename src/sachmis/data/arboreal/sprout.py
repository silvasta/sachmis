from pydantic import BaseModel, Field, PrivateAttr

from ..conversation import ConversationDAG, Prompt, Response
from .base import ArborealTracker


class Sprout(BaseModel):
    """Runtime Container for 1 DAG"""

    tree_tracker: ArborealTracker

    # and most likely (lightweigt tracker of tree that provides data)
    _graph: ArborealTracker | None = PrivateAttr(default=None)

    dag: ConversationDAG
    prompts: dict[str, Prompt] = Field(default_factory=dict)
    responses: dict[str, Response] = Field(default_factory=dict)


class SproutSession(BaseModel):
    sprouts: dict[str, Sprout] = Field(default_factory=dict)
