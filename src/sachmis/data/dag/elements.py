"""
Create the Edges and Nodes for the SproutDAG

- Store full Data of Prompt and Response

"""

__all__: list[str] = [
    "SproutEdge",
    "SproutNode",
    "PromptNode",
    "ResponseNode",
    "ConversationNode",
]

from typing import Annotated, Literal, Self

from pydantic import Field

from ..conversation import Conversation, Prompt, Response
from .base import Edge, Node


class SproutEdge(Edge):
    """Intended to apply Status or Weight to SproutEdge"""


type SproutNode = Annotated[
    PromptNode | ResponseNode, Field(discriminator="partition")
]


class ConversationNode(Node):
    """Base Node for Prompt and Response"""

    @property
    def sprout_id(self) -> int:
        return self._data.sprout_id

    def sprout_stem(self) -> str:
        return self._data.sprout_stem

    @property
    def _data(self) -> Conversation:
        raise NotImplementedError


class PromptNode(ConversationNode):
    partition: Literal["P"] = "P"
    prompt: Prompt

    @property
    def _data(self) -> Prompt:
        return self.prompt

    @classmethod
    def from_prompt(cls, prompt: Prompt) -> Self:
        return cls(uuid=prompt.unique_id, prompt=prompt)


class ResponseNode(ConversationNode):
    partition: Literal["R"] = "R"
    response: Response

    @property
    def _data(self) -> Response:
        return self.response

    @classmethod
    def from_response(cls, response: Response) -> Self:
        return cls(uuid=response.unique_id, response=response)
