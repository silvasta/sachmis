"""
Conversation - Prompt and Response dialog represented as bipartite DAG

- Main purpose is the Data Management of Chats by Prompt and Response
- Backbone for stable and secure Operation is the Graph Structure

They will finally merge in 'fusion' and perform under Sprout.

"""

__all__: list[str] = [
    "BipartiteDAG",
    "ConversationDAG",
    "ConversationData",
    "ConversationEdge",
    "ConversationNode",
    "DataDAG",
    "Prompt",
    "PromptTransitionRules",
    "Response",
    "ResponseTransitionRules",
    "SproutSelectData",
    "SelectedSproutData",
]

from .base import ConversationData
from .base_dag import BipartiteDAG
from .dag import ConversationDAG, ConversationEdge, ConversationNode
from .fusion import DataDAG, SelectedSproutData, SproutSelectData
from .prompt import Prompt
from .response import Response
from .rules import PromptTransitionRules, ResponseTransitionRules
