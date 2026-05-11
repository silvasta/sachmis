from functools import singledispatchmethod
from pathlib import Path
from typing import Self

from loguru import logger
from pydantic import Field
from sstcore.exceptions import NotImplementedDispatchError

from sachmis.data.files import Conversation, ConversationTreeNode

from ...exceptions import PromptError
from ..conversation.prompt import Prompt
from ..conversation.response import Response
from .base import Arboreal


def recursive_conversation_tree(
    current_sprout: Conversation,
) -> ConversationTreeNode:

    branch_nodes: list[ConversationTreeNode] = []

    for next_branch in current_sprout.get_successor():
        if not next_branch.get_successor():
            return current_sprout.as_tree_node()
        branch_nodes.append(recursive_conversation_tree(next_branch))

    return current_sprout.as_tree_node(branch_nodes)


class Tree(Arboreal):
    """Top element inside Forest: entry point for every conversation"""

    root_prompt: Prompt
    tree_stem: str
    # LATER: local_id

    prompts: dict[str, Prompt] = Field(default_factory=dict)
    # TODO: model validate, n_prompts >=1
    responses: dict[str, Response] = Field(default_factory=dict)

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Tree - Custom Functions and Attributes
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    def sample_conversation_tree(self):
        return recursive_conversation_tree(current_sprout=self.root_prompt)

    def find_prompt_by_stem(self, stem: str) -> Prompt | None:
        for prompt in self.prompts.values():
            if prompt._compose_stem() == stem:
                logger.debug(f"found {prompt.desc}")
                return prompt

    def find_response_by_stem(self, stem: str) -> Response | None:
        for response in self.responses.values():
            if response._compose_stem() == stem:
                logger.debug(f"found {response.desc}")
                return response
        logger.debug(f"failed for: {stem=}")

    @classmethod
    def create(cls, prompt: Prompt, tree_stem: str = "") -> Self:
        """Create new Tree with single Sprout attached"""
        tree_stem: str = tree_stem or prompt.slug_topic
        tree: Self = cls(root_prompt=prompt, tree_stem=tree_stem)
        tree.prompts[prompt.unique_id] = prompt
        logger.debug(f"Created:{tree.desc}")
        return tree

    @singledispatchmethod
    def attach(self, target: Prompt | Response):
        raise NotImplementedDispatchError(target.desc)

    @attach.register
    def _(self, target: Prompt):
        """Ensure Ancestor have new added target in Successor"""
        # TODO: some checks specific on Prompt?
        self._confirm_ancestor(target, self.prompts)
        logger.debug(f"Ancestor of Prompt confirmed: {target.desc}")

    @attach.register
    def _(self, target: Response):
        # TODO: some checks specific on Response?
        self._confirm_ancestor(target, self.responses)
        logger.debug(f"Ancestor of Response confirmed: {target.desc}")

    def _confirm_ancestor(self, target: Conversation, registry: dict):
        """Ensure Ancestor have new added target in Successor"""

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
        logger.info("Loading Tree to attach Response")

        with cls.edit_mode(file) as tree:
            tree.attach(target)

        logger.info("All information submitted, Tree closed")

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
        return f"{self.__class__.__name__}: {self.tree_stem}"

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- TODO: Health Check
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
