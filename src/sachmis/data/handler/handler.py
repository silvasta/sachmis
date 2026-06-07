from pathlib import Path
from typing import Literal

from loguru import logger
from sstcore import PathGuard

from ...config import SachmisConfig, get_config
from ...config.models import ModelFamily
from ...exceptions import DataRuntimeError
from ...utils import printer
from ..arboreal import ArborealTracker, Tree
from ..conversation import Prompt

config: SachmisConfig = get_config()

# NEXT:
# NEXT:
# NEXT:
# NEXT:
# NEXT:


# REFACTOR:
# - in out
#   - FileSystem in out
#   - Automatic in out
# - rollout file writer
# - prompt/response handler


class DataHandler:
    """Future interface for other tasks executed with DataManager() as data"""

    tree_id: int = 0  # root number, ids start at 1
    existing_prompts_at_cwd: list[Path] = []
    existing_responses_at_cwd: list[Path] = []
    scanned_models: list[ModelFamily] = []

    _tree_tracker_from_forest: ArborealTracker | None = None
    _tree_tracker_from_tree: ArborealTracker | None = None

    _raw_prompt: Prompt | None = None
    _prompt: Prompt | None = None

    _result_file_paths: list[Path] = []

    def attach_tracker(
        self,
        tracker: ArborealTracker,
        extracted_from: Literal["forest", "tree"],
    ):
        match extracted_from:
            case "forest":
                self._tree_tracker_from_forest: ArborealTracker[Tree] = tracker
            case "tree":
                self._tree_tracker_from_tree: ArborealTracker[Tree] = tracker

    @property
    def existing_conversations(self) -> list[str]:
        return [
            path.stem
            for path in self.existing_prompts_at_cwd
            + self.existing_responses_at_cwd
        ]

    @property
    def tree_tracker(self) -> ArborealTracker:
        if self._tree_tracker_from_tree:
            logger.info("Providing Tree Tracker extracted from Tree")
            return self._tree_tracker_from_tree
        if self._tree_tracker_from_forest:
            logger.info("Providing Tree Tracker extracted from Forest")
            return self._tree_tracker_from_forest
        raise DataRuntimeError("No Tracker Loaded!")

    def attach_prompt(self, prompt: Prompt):
        if config.defaults.log_and_print.data_prompt_attach.printer:
            printer(prompt)
        self.prompt: Prompt = prompt
        logger.debug(f"Prompt attached to: {self.__class__.__name__}")

    @property
    def raw_prompt(self) -> Prompt:
        if self._prompt:  # TODO: check if that has any drawbacks
            logger.info("Providing Prompt instead of raw_prompt")
            return self._prompt
        if self._raw_prompt:
            return self._raw_prompt
        raise DataRuntimeError("Prompt and Prompt not loaded!")

    @property
    def prompt(self) -> Prompt:
        if self._prompt is None:
            raise DataRuntimeError("Prompt not loaded!")
        return self._prompt

    @property
    def result_file_paths(self) -> list[Path]:
        """Get absolute result file paths"""
        return self._result_file_paths

    def result_files(self, root_dir: Path | None = None) -> list[Path]:
        """Compute relative result file paths"""
        return list(
            PathGuard.relative(target=path, root=root_dir, strict=False)
            for path in self.result_file_paths
        )


class FileRollout(DataHandler):
    """Manage Prompt and Response write to Forest dir"""
