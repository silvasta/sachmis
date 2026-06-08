from loguru import logger
from pydantic import BaseModel, Field, PrivateAttr

from ..data.arboreal import ArborealTracker
from ..data.conversation import ConversationDAG, Prompt, Response


class Sprout(BaseModel):
    """Runtime Container for 1 DAG"""

    tree_tracker: ArborealTracker

    # and most likely (lightweight tracker of tree that provides data)
    _tracker: ArborealTracker | None = PrivateAttr(default=None)

    dag: ConversationDAG
    prompts: dict[str, Prompt] = Field(default_factory=dict)
    responses: dict[str, Response] = Field(default_factory=dict)


class SproutSession(BaseModel):
    sprouts: dict[str, Sprout] = Field(default_factory=dict)

    # REFACTOR:
    @property
    def raw_prompt(self) -> Prompt:
        if self._prompt:  # TODO: check if that has any drawbacks
            logger.info("Providing Prompt instead of raw_prompt")
            return self._prompt
        if self._raw_prompt:
            return self._raw_prompt
        raise DataRuntimeError("Prompt and Prompt not loaded!")

    @property
    def prompt(self) -> Prompt:
        if self._prompt is None:
            raise DataRuntimeError("Prompt not loaded!")
        return self._prompt

    def attach_prompt(self, prompt: Prompt):
        if config.defaults.log_and_print.data_prompt_attach.printer:
            printer(prompt)
        self.prompt: Prompt = prompt
        logger.debug(f"Prompt attached to: {self.__class__.__name__}")
