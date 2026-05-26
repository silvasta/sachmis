import uuid
from pathlib import Path
from typing import Literal

from boltons.strutils import slugify
from loguru import logger
from pydantic import BaseModel, Field
from sstcore.utils import SimpleTreeNode

from ...config import SachmisConfig, get_config
from ...exceptions import SachmisDataError
from ...exceptions.data import ConversationGraphError


class ConversationTreeNode(SimpleTreeNode):
    pass


class ConversationData(BaseModel):
    """Data Base of Coversation Part"""

    unique_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    local_id: int = -1  # -1 for not set, starting at 0

    topic: str
    content: str

    @property
    def desc(self):
        return f"{self.__class__.__name__} {self.local_id} with {self.topic=}"

    @property
    def slug_topic(self):  # MOVE: Model validate?
        return slugify(self.topic)

    @property
    def stem(self) -> str:
        return self._compose_stem(strict=True)

    @property
    def _spec_for_stem(self) -> str:
        raise NotImplementedError

    def _compose_stem(self, strict) -> str:
        config: SachmisConfig = get_config()
        if local_id := self.local_id == -1:
            msg = f"Invalid {local_id=}! Needed to create proper stem!"
            if strict:
                raise SachmisDataError(msg)
            logger.error(msg)
        return config.names.sprout_stem.computed(
            locator=f"{self.local_id}",
            spec=self._spec_for_stem,
            topic=self.slug_topic,
        )

    def rollout_path(self, root_dir: Path | None = None, strict=False) -> Path:
        config: SachmisConfig = get_config()
        return config.paths.conversation_file(
            stem=self._compose_stem(strict), root_dir=root_dir
        )

    def write(self, root_dir: Path | None = None, strict=True) -> Path:
        """Rollout to FileSystem"""
        path: Path = self.rollout_path(root_dir, strict)
        path.write_text(self.content)
        logger.info(f"{self.__class__.__name__} written to: {path=}")
        return path


class Conversation(ConversationData):
    """Inheritance Tree Base of Coversation Part"""

    def _get_ancestor(self) -> Conversation | tuple[Conversation] | None:
        raise NotImplementedError

    def _get_successor(self) -> list[Conversation]:
        raise NotImplementedError

    def _ensure_class_swiched(self, other: Conversation):
        """Prompt -> Response -> Promt... required!"""
        if isinstance(other, self.__class__):
            raise ConversationGraphError(bad_link=self.__class__.__name__)

    def get_successor(self) -> list[Conversation]:
        """Direct ancestors, Prompt must have tuple with minimum 1 element,
        Response is growing list that can be empty"""
        for successor in (successors := self._get_successor()):
            self._ensure_class_swiched(successor)
        return successors

    def find_successor(self, unique_id: str) -> Conversation | None:
        for successor in self.get_successor():
            if successor.unique_id == unique_id:
                return successor
            # TODO: recursive? or better from Tree.registry?

    def get_ancestor(
        self, unique_id: str | None = None
    ) -> Conversation | None:
        """Direct ancestor, id for Prompt that answers on multiple Responses,
        Response has always 1, Prompt: None -> root, 1 regular, multiple: use id!"""
        if (ancestor := self._get_ancestor()) is None:
            return None
        if isinstance(ancestor, tuple):
            for father in ancestor:
                if father.unique_id == unique_id:
                    ancestor: Conversation = father
                    break
            else:
                raise SachmisDataError(f"{self.desc}: Invalid {unique_id=}")
        self._ensure_class_swiched(ancestor)
        return ancestor

    def tree_node_id(self, target: Literal["uuid", "local"]):
        match target:
            case "uuid":
                return self.unique_id
            case "local":
                return self.local_id

    def as_tree_node(
        self,
        branches: list[ConversationTreeNode] | None = None,
        target: Literal["uuid", "local"] = "uuid",
    ) -> ConversationTreeNode:
        # IDEA: self.local_id? with ensure: strict2:bool
        return ConversationTreeNode(
            name=self._compose_stem(strict=False),
            id=self.tree_node_id(target),
            branches=branches or [],
        )


def build_conversation_tree(
    root_sprout: Conversation,
    target: Literal["uuid", "local"] = "uuid",
) -> ConversationTreeNode:
    # MOVE: to sstcore.utils???

    return _recursive_conversation_tree(
        current_sprout=root_sprout, visited=set(), target=target
    )


def _recursive_conversation_tree(
    current_sprout: Conversation,
    visited: set[str],
    target: Literal["uuid", "local"] = "uuid",
) -> ConversationTreeNode:

    if current_sprout.unique_id in visited:
        raise SachmisDataError(f"Cylce in Tree! {current_sprout.desc}")

    visited.add(current_sprout.unique_id)

    if not current_sprout.get_successor():
        return current_sprout.as_tree_node(target=target)

    branch_nodes: list[ConversationTreeNode] = []

    for next_branch in current_sprout.get_successor():
        branch_nodes.append(
            _recursive_conversation_tree(
                current_sprout=next_branch,
                visited=visited,
                target=target,
            )
        )

    return current_sprout.as_tree_node(branch_nodes)
