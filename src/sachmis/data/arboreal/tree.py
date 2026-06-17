from loguru import logger
from pydantic import Field

from ...config import SachmisConfig, get_config
from ...utils import printer
from ..conversation import SproutDAG
from .base import Arboreal


class Tree(Arboreal):
    """Top element inside Forest: entry point for every conversation"""

    dag: SproutDAG = Field(default_factory=SproutDAG)

    @property
    def child_info(self):
        return f"{self.dag.n_prompts} Prompts and {self.dag.n_responses} responses"

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Tree - Custom Functions and Attributes
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    def export_dag(self) -> SproutDAG:
        printer(["Tree is Exporting:", self.dag])  # REMOVE:
        # TEST:
        return SproutDAG(**self.dag.model_dump())

    def attach_sub_dag(self, target: str, dag: SproutDAG):

        logger.info("Attaching SproutDAG back to Tree")

        # debug / log
        n_prompts_before: int = self.dag.n_prompts
        n_responses_before: int = self.dag.n_responses
        logger.debug(f"{n_prompts_before=}, {n_responses_before=}")

        # The Function
        self.dag.attach_sprout(target, dag)

        # debug / log
        n_prompts_after: int = self.dag.n_prompts
        n_responses_after: int = self.dag.n_responses
        logger.debug(f"{n_prompts_after=}, {n_responses_after=}")

        # debug / log
        p = f"New Prompts: {n_responses_after - n_responses_before}"
        r = f"New Responses: {n_prompts_after - n_prompts_before}"

        logger.success(f"Tree absorbed DAG: {p}, {r}")

        # debug / log
        config: SachmisConfig = get_config()

        if config.defaults.debug.draw_tree_at_back_attach:
            printer.title("Tree")
            self.draw()

    def draw(self):
        try:
            self.dag.draw()
            printer.title("Draw done...")
        except Exception as error:
            logger.error(f"Draw {type(error)}: {error=}")

    def next_sprout_id(self):
        return self._next_instance_id()
