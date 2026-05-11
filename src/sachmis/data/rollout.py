from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger
from sstcore.data import FileSystemManager, SstFileRegistry

from sachmis.config.model import ModelFamily
from sachmis.data.arboreal import ArborealTracker, Forest, Tree
from sachmis.data.conversation.response import Response

from ..config import SachmisConfig, get_config
from ..utils.parse import parse_raw_models


@dataclass
class ModelData:
    model: ModelFamily
    response: Response


@dataclass
class ModelInfo:
    """Previous Models"""

    tree: ArborealTracker | None = None
    models: list[ModelData] = field(default_factory=list)

    @property
    def model_enums(self) -> list[ModelFamily]:
        return [model_data.model for model_data in self.models]


class FileRollout(FileSystemManager):
    """Manage Prompt and Response write to Forest dir"""

    # LATER: compare PathTree with PromptResponseTree

    def __init__(self, state: SstFileRegistry | None = None):
        config: SachmisConfig = get_config()

        self.file_system_state: SstFileRegistry = state or SstFileRegistry(
            local_root=Path(config.paths.base_dir),
        )
        logger.info("setup complete")
        self.model_info: ModelInfo = self.scan_models()

    def scan_models(self) -> ModelInfo:
        if not (tracker := self.find_tree()):
            return ModelInfo()

        responses: list[Response] = []
        models: list[ModelFamily] = []

        t: Tree = Tree.read_mode(tracker.local_path)
        for path in Path.cwd().glob("*.md"):
            if response := t.find_response_by_stem(path.stem):
                responses.append(response)
                models.append(parse_raw_models([response.model])[0])

        return ModelInfo(
            tree=tracker,
            models=[
                ModelData(model, response)
                for model, response in zip(models, responses, strict=True)
            ],
        )

    def find_tree(self) -> ArborealTracker | None:
        tree_id: int = self.find_tree_id()
        config: SachmisConfig = get_config()
        forest: Forest = Forest.read_mode(config.paths.forest_file)

        return forest.find_tree_by_local_id(tree_id)

    def find_tree_id(self) -> int:
        """No Tree if in root_dir of Forest"""
        config: SachmisConfig = get_config()

        relative_to_base: Path = config.paths.cwd_relative_to_base_dir()
        logger.debug(f"{relative_to_base=}")

        if relative_to_base == Path("."):
            return 0  # root number, ids start at 1

        # WARN:
        tree_dir_name: str = relative_to_base.parts[0]
        tree_name_parts: dict = config.names.tree_file(tree_dir_name)
        local_tree_id: int = tree_name_parts["id"]

        return int(local_tree_id)

    # def set_model_subdir(self, model_name: str):
    # REFACTOR:
    #
    #     match len(paths := list(Path.cwd().glob(f"_{model_name}_"))):
    #         case 0:
    #             raise SachmisDataError("No path to create Model subgroup")
    #         case 1:
    #             model_path: Path = paths[0]
    #         case _:
    #             raise SachmisDataError(
    #                 "Multiple paths to create Model subgroup"
    #             )
    #     self._previous_sprout: Path = model_path
    #     self._write_dir_name: str = model_path.stem
    #     self._next_fs_locator: int = 1
