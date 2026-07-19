"""
Conversation - Prompt and Response dialog represented as bipartite DAG

- Main purpose is the Data Management of Chats by Prompt and Response
- Backbone for stable and secure Operation is the Graph Structure

"""

__all__: list[str] = [
    "Conversation",
    "Prompt",
    "Response",
]

from .base import Conversation
from .prompt import Prompt
from .response import Response
