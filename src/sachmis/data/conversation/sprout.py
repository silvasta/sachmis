import uuid
from pathlib import Path
from typing import Any

from boltons.strutils import slugify
from loguru import logger
from pydantic import BaseModel, Field, model_validator

from ...config import SachmisConfig, get_config
from .order import PromptTypes, ResponseTypes

config: SachmisConfig = get_config()


type SproutTypes = PromptTypes | ResponseTypes

# IDEA: use this as simple printer + data transfer object to DAG?
# from sstcore.utils import SimpleTreeNode
# class SproutNode(SimpleTreeNode):


class Sprout(BaseModel):
    """Beginning of all Prompts and Conversations"""

    unique_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    classifier: SproutTypes

    local_id: int = Field(ge=1)
    topic: str

    original_topic: str | None = None  # Saves the original un-slugified topic

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.local_id})"

    def __str__(self):
        return f"{self.__class__.__name__}_{self.local_id} with {self.topic=}"

    @property
    def stem(self) -> str:
        return self._compose_stem()

    @property
    def _spec_for_stem(self) -> str:
        raise NotImplementedError

    @property
    def content(self) -> str:
        raise NotImplementedError

    def write(self, root_dir: Path | None = None, strict=True) -> Path:
        """Rollout to FileSystem"""
        path: Path = self.rollout_path(root_dir, strict)
        path.write_text(self.content)
        logger.info(f"{self.__class__.__name__} written to: {path=}")
        return path

    def rollout_path(self, root_dir: Path | None = None, strict=False) -> Path:
        return config.paths.conversation_file(
            stem=self._compose_stem(), root_dir=root_dir
        )

    def _compose_stem(self) -> str:
        return config.names.sprout_stem.computed(
            locator=f"{self.local_id}",
            spec=self._spec_for_stem,
            topic=self.topic,
        )

    def tree_node_args(
        self,
        # branches: list[ConversationTreeNode] | None = None,
        # target: Literal["uuid", "local"] = "uuid",
    ) -> Any:
        pass
        # IDEA: self.local_id? with ensure: strict2:bool
        # return ConversationTreeNode(
        #     name=self._compose_stem(strict=False),
        #     id=self.tree_node_id(target),
        #     branches=branches or [],
        # )

    @classmethod
    @model_validator(mode="before")
    def slugify_topic_save_both_use_slug_as_topic(cls, data: Any) -> Any:
        if isinstance(data, dict) and "topic" in data:
            data["original_topic"] = data.get("original_topic", data["topic"])
            data["topic"] = slugify(str(data["topic"]))
        return data


# NEXT:
# NEXT:
# NEXT:
# NEXT:
# NEXT:
# NEXT:
# NEXT:
# class Conversation(ConversationData):
#     """Inheritance Tree Base of Coversation Part"""
#
#     def _get_ancestor(self) -> Conversation | tuple[Conversation] | None:
#         raise NotImplementedError
#
#     def _get_successor(self) -> list[Conversation]:
#         raise NotImplementedError
#
#     def _ensure_class_swiched(self, other: Conversation):
#         """Prompt -> Response -> Promt... required!"""
#         if isinstance(other, self.__class__):
#             raise ConversationGraphError(bad_link=self.__class__.__name__)
#
#     def get_successor(self) -> list[Conversation]:
#         """Direct ancestors, Prompt must have tuple with minimum 1 element,
#         Response is growing list that can be empty"""
#         for successor in (successors := self._get_successor()):
#             self._ensure_class_swiched(successor)
#         return successors
#
#     def find_successor(self, unique_id: str) -> Conversation | None:
#         for successor in self.get_successor():
#             if successor.unique_id == unique_id:
#                 return successor
#             # TODO: recursive? or better from Tree.registry?
#
#     def get_ancestor(
#         self, unique_id: str | None = None
#     ) -> Conversation | None:
#         """Direct ancestor, id for Prompt that answers on multiple Responses,
#         Response has always 1, Prompt: None -> root, 1 regular, multiple: use id!"""
#         if (ancestor := self._get_ancestor()) is None:
#             return None
#         if isinstance(ancestor, tuple):
#             for father in ancestor:
#                 if father.unique_id == unique_id:
#                     ancestor: Conversation = father
#                     break
#             else:
#                 raise SachmisDataError(f"{self.desc}: Invalid {unique_id=}")
#         self._ensure_class_swiched(ancestor)
#         return ancestor
#
#     def tree_node_id(self, target: Literal["uuid", "local"]):
#         match target:
#             case "uuid":
#                 return self.unique_id
#             case "local":
#                 return self.local_id
