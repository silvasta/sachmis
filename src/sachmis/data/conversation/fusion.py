import uuid
from dataclasses import dataclass
from typing import Self

from ...config.models import ModelFamily
from .prompt import Prompt

# NEXT:
# TODO: sprout here???


@dataclass
class SproutSelectData:
    # TASK:
    """
    Provide scanned Data in displayable form until Selection of Models
    - Data will be absorbed by SelectedSproutData
    """

    selector_uuid: str
    selector_display_name: str
    model: ModelFamily
    tree_id: int = 0
    sprout_id: int = 0

    @classmethod
    def from_file(cls, model: ModelFamily, tree_id, sprout_id) -> Self:
        return cls(
            selector_uuid=str(uuid.uuid4()),
            selector_display_name=model.id_cli,
            model=model,
            tree_id=tree_id,
            sprout_id=sprout_id,
        )


@dataclass
class SelectedSproutData:
    # TASK:
    """
    Provide selected Data in condensed form until Init of Models
    - Replaces SproutSelectData after Selection
    - Data will be absorbed by ConversationNode
    """

    model: ModelFamily
    tree_id: int = 0
    sprout_id: int = 0

    @classmethod
    def from_scan(cls, selected: SproutSelectData) -> Self:
        return cls(
            model=selected.model,
            tree_id=selected.tree_id,
            sprout_id=selected.sprout_id,
        )

    @classmethod
    def from_zero(cls, fresh_models: list[ModelFamily]) -> list[Self]:
        return [
            cls(model=model, tree_id=0, sprout_id=0) for model in fresh_models
        ]


@dataclass
class SproutPackage:  # NEXT:
    response_uuid: str
    # intended for multistep during single runtime
    # dag_from_response: ConversationDAG
    prompt: Prompt
    model: ModelFamily
    # NEXT: entire chain of ancestor
    previous_response_uuid: str | None
    previous_remote_id: str | None


# REMOVE:
# class DataDAG(BaseModel):
#     prompts: dict[str, Prompt] = Field(default_factory=dict)
#     responses: dict[str, Response] = Field(default_factory=dict)
#     dag: ConversationDAG = Field(default_factory=ConversationDAG)

# REMOVE:
# def get_response_node(
#     self, sprout: SelectedSproutData
# ) -> ConversationNode:
#     """Find Grandfather of Response and make Selection to Node"""
#     if sprout.sprout_id == 0:
#         raise DataRuntimeError(f"No : {sprout}")
#     if sprout_group := self.dag.find_sprout_group(sprout.sprout_id):
#         return self._filter_out_response(sprout, sprout_group)
#     raise SachmisDataError(f"Missing Selected Model: {sprout}")

# REMOVE:
# def _filter_out_response(
#     self,
#     model_data: SelectedSproutData,  # LATER: open
#     sprout_group: list[ConversationNode],
# ) -> ConversationNode:
#     logger.debug(f"{model_data=} AND {len(sprout_group)=}")
#
#     result: ConversationNode | None = None
#     for node in sprout_group:
#         if node.partition == "P":
#             logger.debug(f"ignoring prompt: {node=}")
#         else:
#             response: Response = self.responses[node.uuid]
#             printer(("Found: ", response))  # REMOVE:
#             if response.model == model_data.model:
#                 logger.success(f"Found: {node=}")
#                 result: ConversationNode = node
#
#     if not result:  # REMOVE:
#         raise SachmisDataError("Missing Response from ConversationNode!")
#     return result

# REMOVE:
# @classmethod
# def init_from(cls, prompt: Prompt) -> Self:
#     prompts: dict[str, Prompt] = {prompt.unique_id: prompt}
#     responses: dict[str, Response] = {}
#     _prompt_node: ConversationNode = cls.prompt_node_from(prompt)
#     dag: ConversationDAG = cls.dag_from(_prompt_node)
#     return cls(prompts=prompts, responses=responses, dag=dag)

# REMOVE:
# @staticmethod
# def dag_from(node: ConversationNode) -> ConversationDAG:
#     return ConversationDAG(
#         nodes=[node],
#         edges=[],
#     )

# REMOVE:
# @staticmethod
# def prompt_node_from(prompt: Prompt) -> ConversationNode:
#     return ConversationNode(
#         uuid=prompt.unique_id,
#         partition="P",
#         sprout_id=prompt.sprout_id,
#         tree_id=prompt.tree_id,
#         topic=prompt.topic,
#     )

# REMOVE:
# @staticmethod
# def response_node_from(response: Response) -> ConversationNode:
#     return ConversationNode(
#         uuid=response.unique_id,
#         partition="R",
#         sprout_id=response.sprout_id,
#         tree_id=response.tree_id,
#         topic=response.topic,
#     )
