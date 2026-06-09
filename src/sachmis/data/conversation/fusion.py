from sachmis.utils import printer
import re
from typing import Self

from loguru import logger
from pydantic import BaseModel, Field

from ...config.models import ModelSelectData
from ...exceptions import SachmisDataError
from .dag import ConversationDAG, ConversationEdge, ConversationNode
from .prompt import Prompt
from .response import Response


# NEXT: move, change, multiple models!!!!!!!!!!!
# NEXT: move, change, multiple models!!!!!!!!!!!
# NEXT: move, change, multiple models!!!!!!!!!!!
# NEXT: move, change, multiple models!!!!!!!!!!!
# NEXT: move, change, multiple models!!!!!!!!!!!
# NEXT: move, change, multiple models!!!!!!!!!!!
@dataclass
class ModelRunData:  # TASK: reduced class after selection
    model: ModelFamily
    tree_id: int = 0
    sprout_id: int = 0


class DataDAG(BaseModel):
    prompts: dict[str, Prompt] = Field(default_factory=dict)
    responses: dict[str, Response] = Field(default_factory=dict)
    dag: ConversationDAG

    def find_response_node(
        self, model_data: ModelSelectData
    ) -> ConversationNode:
        if sprout_group := self.dag.find_sprout_group(model_data.sprout_id):
            return self._filter_response(model_data, sprout_group)
        raise SachmisDataError(f"Missing Selected Model: {model_data}")

    def _filter_response(
        self, model_data: ModelSelectData, sprout_group: list[ConversationNode]
    ) -> ConversationNode:
        logger.debug(f"{model_data=} AND {len(sprout_group)=}")
        result: ConversationNode | None = None
        for node in sprout_group:
            if node.partition == "P":
                logger.debug(f"ignoring prompt: {node=}")
            else:
                response: Response = self.responses[node.id]
                printer(("Found: ", response))  # REMOVE:
                if response.model == model_data.model:
                    logger.success(f"Found: {node=}")
                    result: ConversationNode = node
        if not result:
            raise SachmisDataError("Missing Response from ConversationNode!")
        return result

    @classmethod
    def init_from(cls, prompt: Prompt) -> Self:
        prompts: dict[str, Prompt] = {prompt.unique_id: prompt}
        responses: dict[str, Response] = {}
        _prompt_node: ConversationNode = cls.prompt_from(prompt)
        dag: ConversationDAG = cls.dag_from(_prompt_node)
        return cls(prompts=prompts, responses=responses, dag=dag)

    @staticmethod
    def dag_from(node: ConversationNode) -> ConversationDAG:
        return ConversationDAG(
            nodes=[node],
            edges=[],
        )

    @staticmethod
    def prompt_from(prompt: Prompt) -> ConversationNode:
        return ConversationNode(
            id=prompt.unique_id,
            partition="P",
            local_id=prompt.sprout_id,
            name=prompt.topic,
        )

    @staticmethod
    def response_from(response: Response) -> ConversationNode:
        return ConversationNode(
            id=response.unique_id,
            partition="R",
            local_id=response.sprout_id,
            name=response.topic,
        )
