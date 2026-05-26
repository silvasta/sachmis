from pathlib import Path
from typing import Literal

from loguru import logger
from sstcore import PathGuard
from sstcore.data import SstFileRegistry

from ..config import SachmisConfig, get_config
from ..config.model import ModelFamily
from ..exceptions import DataRolloutError, DataRuntimeError, SachmisDataError
from ..utils import model_from_unique, printer
from .arboreal import ArborealTracker, Tree
from .conversation import Prompt, PromptData

config: SachmisConfig = get_config()


class FileHandler:
    """Future interface for other tasks executed with DataManager() as data"""

    tree_id: int = 0  # root number, ids start at 1
    existing_prompts_at_cwd: list[Path] = []
    existing_responses_at_cwd: list[Path] = []
    parsed_models: list[ModelFamily] = []

    _tree_tracker_from_forest: ArborealTracker | None = None
    _tree_tracker_from_tree: ArborealTracker | None = None

    _raw_prompt: PromptData | None = None
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
    def tree_tracker(self) -> ArborealTracker:
        if self._tree_tracker_from_tree:
            logger.info("Providing Tree Tracker extracted from Tree")
            return self._tree_tracker_from_tree
        if self._tree_tracker_from_forest:
            logger.info("Providing Tree Tracker extracted from Forest")
            return self._tree_tracker_from_forest
        raise DataRuntimeError("No Tracker Loaded!")

    def attach_prompt(self, prompt: Prompt):
        if config.defaults.log_and_print.data_handler_prompt.printer:
            printer(prompt)
        self.prompt: Prompt = prompt
        logger.debug(f"Prompt attached to: {self.__class__.__name__}")

    @property
    def raw_prompt(self) -> PromptData:
        if self._prompt:  # TODO: check if that has any drawbacks
            logger.info("Providing Prompt insted of raw_prompt")
            return self._prompt
        if self._raw_prompt:
            return self._raw_prompt
        raise DataRuntimeError("PromptData and Prompt not loaded!")

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


class FileRollout(FileHandler):
    """Manage Prompt and Response write to Forest dir"""

    # LATER: compare PathTree with PromptResponseTree

    _prompt_written = False
    _write_dir_name: str = ""

    @property
    @PathGuard.dir
    def write_dir(self):
        return Path.cwd() / self._write_dir_name

    @property
    def local_root(self) -> Path:
        return self.file_system_state.local_root

    def __init__(self, state: SstFileRegistry | None = None):
        self.file_system_state: SstFileRegistry = (
            state or SstFileRegistry.setup_at(local_root=config.paths.base_dir)
        )

        self.tree_id: int = self.extract_tree_id()
        logger.info(f"Using {self.tree_id=}")

        self.scan_folder()
        logger.info(self.scan_statistics)

        self._raw_prompt: PromptData = self.load_raw_prompt()

    def load_raw_prompt(self) -> PromptData:
        return PromptData.load_from_path()

    @staticmethod
    def extract_tree_id() -> int:
        """Tree id or zero if in root_dir of Forest"""

        if (relative_to_base := config.paths.cwd_to_base_dir()) == Path():
            return 0
        logger.debug(f"{relative_to_base=}")
        try:
            tree_dir_name: str = relative_to_base.parts[0]
            tree_name_parts: dict = config.names.tree_file(tree_dir_name)
            extracted_id: str = tree_name_parts["id"]
            return int(extracted_id)
        except (ValueError, KeyError) as error:
            logger.error(f"Problems while parsing: {error=}")

        raise DataRolloutError(f"Tree Not Found from: {relative_to_base=}")

    @property
    def scan_statistics(self) -> str:
        return (
            f"Found {len(self.existing_prompts_at_cwd)} Prompts, "
            f"{len(self.existing_responses_at_cwd)} Responses "
            f"and parsed {len(self.parsed_models)} Models."
        )

    def scan_folder(self):
        """Backward parse file names in current folder"""

        for path in Path.cwd().glob("*.md"):
            try:  # LATER: check for (nested) folders?
                name_parts: dict = config.names.sprout_stem(path)
                if (spec := name_parts[key_to_check := "spec"]) == "prompt":
                    self.existing_prompts_at_cwd.append(path)
                    logger.debug(f"attach to prompts: {path=}")
                elif model := model_from_unique(spec):
                    self.existing_responses_at_cwd.append(path)
                    self.parsed_models.append(model)
                    logger.debug(f"attach {model=} and response from: {path=}")
                else:
                    logger.debug(f"ignoring {path=}")
            except ValueError:
                logger.debug(f"Failed to parse: {path=}")
            except KeyError:
                logger.error(f"{key_to_check=} failed for: {path=}")

    def rotate_prompt(self) -> Path:
        # HACK: how to get the prompt here? or just the command to process? where to send path?
        prompt_path: Path = self.prompt.rollout_path(root_dir=self.write_dir)
        PathGuard.rotate(
            source=self.input_prompt_path, target=prompt_path, reset=True
        )
        logger.debug(f"prompt rotated: {prompt_path=}")
        if self.write_dir != Path.cwd():
            (self.write_dir / config.names.prompt).touch()
            logger.debug("new empty prompt in new write_dir")
        return prompt_path

    def save_response(self):
        pass

    def set_model_subdir(self, model_name: str):
        # REFACTOR: match to new structure
        match len(paths := list(Path.cwd().glob(f"_{model_name}_"))):
            case 0:
                raise SachmisDataError("No path to create Model subgroup")
            case 1:
                model_path: Path = paths[0]
            case _:
                raise SachmisDataError(
                    "Multiple paths to create Model subgroup"
                )
        self._previous_sprout: Path = model_path
        self._write_dir_name: str = model_path.stem  # TODO: keep
        self._next_fs_locator: int = 1
        # REFACTOR: match to new structure
