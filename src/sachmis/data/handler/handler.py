import uuid
from abc import abstractmethod
from pathlib import Path

from loguru import logger
from sstcore import PathGuard

from ...config import SachmisConfig, get_config
from ...exceptions import PromptError, SachmisDataError
from ...utils import printer
from ..arboreal import ArborealTracker, Tree
from ..conversation import (
    ConversationNode,
    DataDAG,
    Prompt,
    SelectedSproutData,
    SproutSelectData,
)

config: SachmisConfig = get_config()


class DataHandler:
    """Provide input/output data from Sprout to Forest or Rollout"""

    scanned_tree_id: int = 0
    _prompt_text: str = ""

    _topic: str = ""
    _tree_tracker: ArborealTracker[Tree] | None = None
    _initial_prompt: Prompt | None = None
    _dag_of_entire_tree: DataDAG | None = None

    _growing_dag: DataDAG | None = None
    _sprout_registry: dict[str, ConversationNode] = {}

    _result_files: list[Path] = []

    # NEXT:
    @abstractmethod
    def prepare_package(self, selected_model: SelectedSproutData) -> DataDAG:
        """Load DataDAG or whatever"""
        next_id = str(uuid.uuid4())
        previous_response_node: ConversationNode = (
            self.tree_dag.find_response_node(selected_model)
        )
        response_node: ConversationNode = self._create_response_node(next_id)

        self.growing_dag.dag.attach_leaf(
            anchor=previous_response_node.id, node=response_node
        )

        self._sprout_registry[next_id] = previous_response_node
        return info

    def _create_response_node(self, next_id) -> ConversationNode:
        return ConversationNode(
            uuid=next_id,
            partition="R",
            sprout_id=self.prompt.sprout_id,
            tree_id=self.prompt.tree_id,
            topic=self.prompt.topic,
        )

    @abstractmethod
    def process_response(self, **kwargs):
        """Process the received Prompt or Response with your Schema"""
        # NEXT: preprocessing: general
        self._handle_response_by_responsibility()

    # NEXT: back to tree
    def export_dag(self):
        """Send only the newly created part of the DAG"""
        raise NotImplementedError

    @abstractmethod
    def _handle_response_by_responsibility(self, **kwargs):
        raise NotImplementedError

    @property
    def prompt(self) -> Prompt:
        if not self._initial_prompt:
            raise SachmisDataError("No Initial Prompt loaded, wait for Tree")
        return self._initial_prompt

    @property
    def growing_dag(self) -> DataDAG:
        if not self._growing_dag:
            raise SachmisDataError("No DAG loaded, can't provide DAG")
        return self._growing_dag

    @property
    def tree_dag(self) -> DataDAG:
        if not self._dag_of_entire_tree:
            raise SachmisDataError("No DAG loaded, can't provide DAG")
        return self._dag_of_entire_tree

    @property
    def prompt_text(self):
        """Ensure the provided content is valid and avaliable"""
        if not (ensured_text := self._prepare_prompt_text()):
            name: str = self.__class__.__name__
            PromptError(f"{name} has no valid Prompt Data!")
        return ensured_text

    @property
    def tree_id(self) -> int:
        return self.tree_tracker.local_id

    @property
    def topic(self):
        """Ensure Handler has loaded a valid topic"""
        if not (topic := self._topic):
            name: str = self.__class__.__name__
            PromptError(f"{name} has no valid Prompt Topic!")
        return topic

    @property
    def tree_tracker(self) -> ArborealTracker:
        if not self._tree_tracker:
            raise SachmisDataError("Missing Tracker!")
        return self._tree_tracker

    @abstractmethod
    def _prepare_prompt_text(self):
        """Provide the prepared content for the Prompt"""

    def result_files_relative(
        self, root_dir: Path | None = None
    ) -> list[Path]:
        """Provide relative Paths of already written result files"""
        return list(
            PathGuard.relative(target=path, root=root_dir, strict=False)
            for path in self._result_files
        )

    @property
    def result_file_paths(self) -> list[Path]:
        """Provide absolute Paths of already written result files"""
        return self._result_files

    # INFO: 1
    def attach_tracker(self, tracker: ArborealTracker[Tree]):
        self._tree_tracker: ArborealTracker[Tree] = tracker

    # INFO: 1
    def attach_tree_data(self, sprout_id: int, full_dag: DataDAG):
        self._initial_prompt: Prompt = Prompt.from_text(
            content=self.prompt_text, sprout_id=sprout_id, topic=self.topic
        )
        self._dag_of_entire_tree: DataDAG = full_dag
        self._growing_dag: DataDAG = DataDAG.init_from(self._initial_prompt)

        printer.special("Tree DAG")
        printer(self._dag_of_entire_tree)
        printer.special("Sprout DAG")
        printer(self._growing_dag)

        logger.info(f"DAG attached from Tree to {self.__class__.__name__}")

    @abstractmethod
    def models(self) -> list[SproutSelectData]:
        """Provide subset of Models according to observed Data state"""
