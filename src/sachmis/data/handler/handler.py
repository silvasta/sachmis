import uuid
from abc import abstractmethod
from pathlib import Path

from loguru import logger
from sstcore import PathGuard

from ...config import SachmisConfig, get_config
from ...config.models import ModelSelectData
from ...exceptions import PromptError, SachmisDataError
from ..arboreal import ArborealTracker, Tree
from ..conversation import ConversationDAG, DataDAG, Prompt, Response

config: SachmisConfig = get_config()


class DataHandler:
    """Provide input/output data from Sprout to Forest or Rollout"""

    scanned_tree_id: int = 0
    _result_files: list[Path] = []
    _prompt_text: str = ""
    _topic: str = ""
    _tree_tracker: ArborealTracker[Tree] | None = None

    _initial_prompt: Prompt | None = None
    _dag_of_entire_tree: DataDAG | None = None

    _sprout_registry: dict[str, ModelSelectData] = {}

    def attach_tracker(self, tracker: ArborealTracker[Tree]):
        self._tree_tracker: ArborealTracker[Tree] = tracker

    # NEXT: model registry, assign uuid, use later for response
    # - plus create data bag with files, role, .. everything

    def attach_tree_data(self, sprout_id: int, full_dag: DataDAG):
        self._initial_prompt: Prompt = Prompt.from_text(
            content=self.prompt_text, sprout_id=sprout_id, topic=self.topic
        )
        self._dag_of_entire_tree: DataDAG = full_dag
        logger.info(f"DAG attached from Tree to {self.__class__.__name__}")

    @abstractmethod
    def models(self) -> list[ModelSelectData]:
        """Provide subset of Models according to observed Data state"""

    # NEXT:
    @abstractmethod
    def prepare_package(self, model_data: ModelSelectData) -> DataDAG:
        """Load DataDAG or whatever"""
        response_id = str(uuid.uuid4())
        # TODO: data
        # - model
        # - chain [P,R,P,R,...] of previous livin responses
        # - DAG with here new created prompt as head,
        # - response_id for head of new dag
        self._sprout_registry[response_id] = info
        # TODO: info
        # - model
        # - ?
        return info

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
    def prompts(self) -> dict[str, Prompt]:
        if not self._dag_of_entire_tree:
            raise SachmisDataError("No DAG loaded, can't provide Prompt")
        return self._dag_of_entire_tree.prompts

    @property
    def responses(self) -> dict[str, Response]:
        if not self._dag_of_entire_tree:
            raise SachmisDataError("No DAG loaded, can't provide Response")
        return self._dag_of_entire_tree.responses

    @property
    def dag(self) -> ConversationDAG:
        if not self._dag_of_entire_tree:
            raise SachmisDataError("No DAG loaded, can't provide DAG")
        return self._dag_of_entire_tree.dag

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
