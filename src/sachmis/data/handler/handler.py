import uuid
from abc import abstractmethod
from pathlib import Path

from loguru import logger
from sstcore import PathGuard

from sachmis.data.conversation.fusion import SproutPackage

from ...config import SachmisConfig, get_config
from ...exceptions import DataRuntimeError, PromptError, SachmisDataError
from ...utils import printer
from ..arboreal import ArborealTracker, Tree
from ..conversation import (
    ConversationNode,
    DataDAG,
    Prompt,
    Response,
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

    # TODO: improve property and access (.._dag.dag?)
    _dag_of_entire_tree: DataDAG | None = None
    _growing_dag: DataDAG | None = None

    # LATER: more advanced registry, use some data type!
    # - like 2-3 properties that automatically answer the questions
    _sprout_registry: dict[str, str | None] = {}

    _result_files: list[Path] = []

    def provide_grandfather_uuid(self, grand_child_uuid: str) -> str | None:
        """Find Response before, so far without MultiPrompt support"""

        for edge in self.tree_dag.dag.edges:
            if edge.target == grand_child_uuid:
                return edge.source

    # NEXT:
    @abstractmethod
    def prepare_package(self, selection: SelectedSproutData) -> SproutPackage:
        """Load SproutPackage with everything needed for a new DAG"""

        if previous_response_uuid := self._find_ancestor_uuid(selection):
            remote_id: str | None = self.find_previous_response(
                previous_response_uuid
            )
            logger.success("found previous_remote_id")
        else:
            remote_id = None

        next_uuid: str = self._attach_new_node_to_root_prompt()
        self._sprout_registry[next_uuid] = previous_response_uuid
        logger.debug(f"attached to sprout_registry: {previous_response_uuid=}")

        return SproutPackage(
            response_uuid=next_uuid,
            dag_from_response=self.growing_dag.dag.copy_subtree(next_uuid),
            prompt=Prompt.clone(self.prompt),
            previous_response_uuid=previous_response_uuid,
            previous_remote_id=remote_id,
        )

    def find_previous_response(
        self, previous_response_uuid: str
    ) -> str | None:
        if previous_response_uuid in self.tree_dag.responses:
            previous: Response = self.tree_dag.responses[
                previous_response_uuid
            ]
            return previous.remote_id
        raise DataRuntimeError("Root should not end up here...")

    def _find_ancestor_uuid(self, selection: SelectedSproutData) -> str | None:
        # LATER: find entire Linear Tree of Ancestors
        if selection.sprout_id == 0:  # case root (or fail)
            return None
        previous: ConversationNode = self.tree_dag.get_response_node(selection)
        if previous.uuid not in self.tree_dag.dag.nodes:
            raise SachmisDataError(f"Invalid uuid from {selection=}")
        return previous.uuid

    def _attach_new_node_to_root_prompt(self) -> str:
        new_response_uuid = str(uuid.uuid4())
        self.growing_dag.dag.attach_leaf(
            target_uuid=self.prompt.unique_id,
            new_node=self._create_response_node(new_response_uuid),
        )  # WARN: rebuild the Graph?
        logger.debug(f"response_node attached with {new_response_uuid=}")
        return new_response_uuid

    def _create_response_node(self, uuid) -> ConversationNode:
        return ConversationNode(
            uuid=uuid,
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
            content=self.prompt_text,
            sprout_id=sprout_id,
            topic=self.topic,
            tree_id=self.tree_id,
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
