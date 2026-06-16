from loguru import logger

from sachmis.utils import printer

from ..conversation import SproutDAG
from .base import Arboreal


class Tree(Arboreal):
    """Top element inside Forest: entry point for every conversation"""

    dag: SproutDAG

    @property
    def child_info(self):
        return f"{self.dag.n_prompts} Prompts and {self.dag.n_responses} responses"

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Tree - Custom Functions and Attributes
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    def export_dag(self) -> SproutDAG:
        printer(["Tree is Exporting:", self.dag])  # REMOVE:
        return SproutDAG(**self.dag.model_dump())

    def attach_sub_dag(self, target, dag: SproutDAG):

        # NEXT:
        # NEXT:
        # NEXT:
        # NEXT:
        # for id, prompt in dag.prompts.items():
        #     if id in self.prompts:
        #         logger.error(f"Doubled Prompt: {prompt}")
        #
        # for id, response in dag.responses.items():
        #     if id in self.responses:
        #         logger.error(f"Doubled Response: {response}")
        #
        # self.data_dag.dag.attach_sprout(target, dag.dag)
        # logger.success("Tree absorbed DAG")

        self.draw()

    def draw(self):
        try:
            self.dag.draw()
        except Exception as error:
            logger.error(f"Draw {error=} {type(error)}")

    def next_sprout_id(self):
        return self._next_instance_id()
