from pathlib import Path

from loguru import logger
from pydantic import Field

from ..conversation import ConversationDAG, Prompt, Response
from .base import Arboreal
from .sprout import Sprout


class Tree(Arboreal):
    """Top element inside Forest: entry point for every conversation"""

    tree_stem: str

    prompts: dict[str, Prompt] = Field(default_factory=dict)
    responses: dict[str, Response] = Field(default_factory=dict)

    dag: ConversationDAG = Field(default_factory=dict)

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Tree - Custom Functions and Attributes
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    def find_conversation_by_stem(
        self, stems: list[str], target_uuid: str
    ) -> Sprout:
        sprout_root_dag: ConversationDAG = self.dag.copy_subtree(target_uuid)

        result = Sprout(
            tree_tracker=self.tracker_info,
            dag=sprout_root_dag,
            prompts={
                prompt.unique_id: prompt
                for stem in stems
                for prompt in self.prompts.values()
                if prompt.stem == stem
            },
            responses={
                response.unique_id: response
                for stem in stems
                for response in self.responses.values()
                if response.stem == stem
            },
        )
        return result

    @classmethod
    def file_attach(cls, file: Path, target: Prompt | Response):
        logger.info("Loading Tree to attach Response")

        with cls.edit_mode(file) as tree:
            tree.attach(target)

        logger.info("All information submitted, Tree closed")

    def attach(self, target: Prompt | Response) -> None:
        """Attach a Prompt or Response and sync it to the DAG."""
        from ..conversation import ConversationNode

        # 1. Store in the respective data dictionary
        if isinstance(target, Prompt):
            self.prompts[target.unique_id] = target
            partition = "P"
        elif isinstance(target, Response):
            self.responses[target.unique_id] = target
            partition = "R"
        else:
            raise TypeError(f"Cannot attach {type(target)} to Tree.")

        # 2. Append to the DAG representation
        node = ConversationNode(
            id=target.unique_id,
            partition=partition,
            local_id=target.local_id,
            name=target.topic if isinstance(target, Prompt) else target.model,
        )
        self.dag.nodes.append(node)

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
        return f"{self.n_prompts} Prompts and  {self.n_responses} responses"

    @property
    def desc(self):
        return f"{self.name}: {self.tree_stem}"

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- TODO: Health Check
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
