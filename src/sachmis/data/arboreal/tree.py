from functools import singledispatchmethod
from pathlib import Path
from typing import Self

from loguru import logger
from pydantic import Field
from sstcore.exceptions import NotImplementedDispatchError

from ...exceptions import PromptError
from ..conversation import ConversationBag
from ..conversation.base import Conversation, build_conversation_tree
from ..conversation.prompt import Prompt, PromptData
from ..conversation.response import Response
from .base import Arboreal


class Tree(Arboreal):
    """Top element inside Forest: entry point for every conversation"""

    root_prompt: Prompt
    tree_stem: str

    prompts: dict[str, Prompt] = Field(default_factory=dict)
    responses: dict[str, Response] = Field(default_factory=dict)

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Tree - Custom Functions and Attributes
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    def find_conversation_by_stem(self, stems: list[str]) -> ConversationBag:
        result = ConversationBag(
            prompts=[
                prompt
                for stem in stems
                for prompt in self.prompts.values()
                if prompt.stem == stem
            ],
            responses=[
                response
                for stem in stems
                for response in self.responses.values()
                if response.stem == stem
            ],
        )
        result.log_and_print()
        return result

    @classmethod
    def with_prompt(
        cls,
        prompt: PromptData,
        tree_file: Path,
        local_id: int,
        tree_stem: str = "",
    ) -> Self:
        """Create new Tree with single Sprout attached"""
        prompt: Prompt = Prompt.upgrade_from_raw(
            raw_prompt=prompt, local_id=local_id, ancestor=None
        )
        tree: Self = cls.with_tracker(
            path=tree_file,
            local_id=local_id,
            root_prompt=prompt,
            tree_stem=tree_stem or prompt.slug_topic,
        )
        tree.prompts[prompt.unique_id] = prompt
        logger.debug(f"Created: {tree.desc}")

        return tree

    @singledispatchmethod
    def attach(self, target: Prompt | Response):
        # NEXT:
        raise NotImplementedDispatchError(target.desc)

    @attach.register
    def _(self, target: Prompt):
        # NEXT:
        """Ensure Ancestor have new added target in Successor"""
        # TODO: some checks specific on Prompt?
        self._confirm_ancestor(target, self.prompts)
        logger.debug(f"Ancestor of Prompt confirmed: {target.desc}")

    @attach.register
    # NEXT:
    def _(self, target: Response):
        # TODO: some checks specific on Response?
        self._confirm_ancestor(target, self.responses)
        logger.debug(f"Ancestor of Response confirmed: {target.desc}")

    def _confirm_ancestor(self, target: Conversation, registry: dict):
        # NEXT:
        """Ensure Ancestor have new added target in Successor"""

        # TASK: confirm

        logger.debug(f"Confirming ancestor: {target.desc}")

        if (target_ancestor := target.single_ancestor()) is None:
            raise PromptError(f"Ancestor not found in Prompt: {target.desc}")

        if not (tree_ancestor := registry.get(target_ancestor.unique_id)):
            raise PromptError(f"Ancestor not found in Registry: {target.desc}")

        # LATER: More checks? and prompt with multi predecessors

        if _target_in_tree := tree_ancestor.find_successor(target.unique_id):
            logger.debug(f"Already in Tree: {target.desc}")
        else:
            registry[target.unique_id] = target
            logger.debug(f"Added to Tree: {target.desc}")

    @classmethod
    def file_attach(cls, file: Path, target: Prompt | Response):
        # NEXT:
        logger.info("Loading Tree to attach Response")

        with cls.edit_mode(file) as tree:
            tree.attach(target)

        logger.info("All information submitted, Tree closed")

    def sample_conversation_tree(self):
        return build_conversation_tree(root_sprout=self.root_prompt)

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Arboreal - Access to Members
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    @property
    def n_prompts(self) -> int:
        return len(self.prompts)

    @property
    def n_responses(self) -> int:
        return len(self.responses)

    @property
    def child_info(self):
        return f"{self.n_prompts} Promts and  {self.n_responses} responses"

    @property
    def desc(self):
        return f"{self.name}: {self.tree_stem}"

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- TODO: Health Check
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
