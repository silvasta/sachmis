from dataclasses import dataclass, field

from loguru import logger

from ...config import SachmisConfig, get_config
from ...utils import printer
from .base import Conversation, ConversationData, ConversationTreeNode
from .prompt import Prompt, PromptData
from .response import Response, ResponseData

config: SachmisConfig = get_config()


@dataclass
class ConversationBag:  # MOVE: to own module if it grows even more
    """Container for Prompts and Responses"""

    prompts: list[Prompt] = field(default_factory=list)
    responses: list[Response] = field(default_factory=list)

    @property
    def n_prompts(self):
        return len(self.prompts)

    @property
    def n_responses(self):
        return len(self.responses)

    def log_and_print(self):
        text = f"Containing {self.n_prompts=}, {self.n_responses=}"
        if config.defaults.log_and_print.conversation_bag.printer:
            printer(text)
        if config.defaults.log_and_print.conversation_bag.log:
            logger.info(text)


__all__: list[str] = [
    "Conversation",
    "ConversationBag",
    "ConversationData",
    "ConversationTreeNode",
    "Prompt",
    "PromptData",
    "Response",
    "ResponseData",
]
