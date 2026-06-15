from loguru import logger
from pydantic import Field

from sachmis.utils import printer

from ..conversation import ConversationDAG, DataDAG, Prompt, Response
from .base import Arboreal


class Tree(Arboreal):
    """Top element inside Forest: entry point for every conversation"""

    data_dag: DataDAG = Field(default_factory=DataDAG)

    @property
    def prompts(self) -> dict[str, Prompt]:
        return self.data_dag.prompts

    @property
    def responses(self) -> dict[str, Response]:
        return self.data_dag.responses

    @property
    def dag(self) -> ConversationDAG:
        return self.data_dag.dag

    @property
    def n_prompts(self) -> int:
        return len(self.prompts)

    @property
    def n_responses(self) -> int:
        return len(self.responses)

    @property
    def child_info(self):
        return f"{self.n_prompts} Prompts and {self.n_responses} responses"

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Tree - Custom Functions and Attributes
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    def export_dag(self) -> DataDAG:
        printer(self.data_dag)  # REMOVE:
        return DataDAG(**self.data_dag.model_dump())

    def attach_sub_dag(self, target, dag: DataDAG):

        for id, prompt in dag.prompts.items():
            if id in self.prompts:
                logger.error(f"Doubled Prompt: {prompt}")

        for id, response in dag.responses.items():
            if id in self.responses:
                logger.error(f"Doubled Response: {response}")

        self.data_dag.dag.attach_sprout(target, dag.dag)
        logger.success("Tree absorbed DAG")

        self.draw()

    def draw(self):
        try:
            self.dag.draw()
        except Exception as error:
            logger.error(f"Draw {error=} {type(error)}")

    def next_sprout_id(self):
        return self._next_instance_id()
