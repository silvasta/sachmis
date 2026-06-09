from pydantic import BaseModel, Field

from .dag import ConversationDAG
from .prompt import Prompt
from .response import Response


class DataDAG(BaseModel):
    prompts: dict[str, Prompt] = Field(default_factory=dict)
    responses: dict[str, Response] = Field(default_factory=dict)
    dag: ConversationDAG
