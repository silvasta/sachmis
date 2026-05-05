from pathlib import Path
from typing import Self

from loguru import logger
from pydantic import Field
from sstcore.data import SstFileRegistry

from sachmis.exceptions import SachmisDataError

from ...config import SachmisConfig, get_config
from ..files import CampManager, UploadRegistry
from ..prompt import Prompt
from .base import ArborealDisk, ArborealTracker
from .tree import Tree


class Forest(ArborealDisk[Tree]):
    """Master tree file: Data of all Trees and Sprouts in base"""

    roles: SstFileRegistry

    files: UploadRegistry
    images: SstFileRegistry

    sprouts: dict[str, set[Path]] = Field(
        default_factory=dict
    )  # tree-id : sprout location on filesystem

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Arboreal - Access to Members
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    @property
    def n_trees(self) -> int:
        """Calculated by num trackers"""
        return self.n_children

    @property
    def trees(self) -> list[ArborealTracker]:
        """Serialized part of registry with UUID and ArborealTracker"""
        return self.registry.all_trackers

    @property
    def loaded_trees(self) -> list[Tree]:
        return self.registry.all_members

    @property
    def missing_trees(self) -> list[ArborealTracker]:
        return self.registry.tracker_with_invalid_paths

    def n_sprouts(self) -> int:
        return sum(tree.n_sprouts for tree in self.loaded_trees)

    @property
    def local_tree_ids(self) -> list[int]:
        return [t.local_id for t in self.registry.all_trackers]

    @property
    def unique_tree_ids(self) -> list[str]:
        return [t.unique_id for t in self.registry.all_trackers]

    def find_tree_by_unique_id(self, id: str) -> ArborealTracker | None:
        return self.registry.find_tracker(id)

    # TODO: Tree or Tracker?

    def find_tree_by_local_id(self, id: str) -> ArborealTracker | None:
        return self.registry.find_tracker_by_local_id(id)

    def provide_tree(self, previous_sprout: Path) -> ArborealTracker:
        for tree_id, paths in self.sprouts.items():
            if previous_sprout in paths:
                if tracker := self.find_tree_by_unique_id(tree_id):
                    return tracker
        logger.error(f"{previous_sprout=}")
        logger.error(self.sprouts)
        raise SachmisDataError(f"No Tree in Forest for: {previous_sprout=}")

    def attach_sprout_paths(self, tree_id: str, sprout_path: Path):
        if tree_id not in self.sprouts:
            logger.info("Forest tracks Sprout from new Tree")
            self.sprouts[tree_id]: set[Path] = set()
        if sprout_path in self.sprouts.get(tree_id, {}):
            logger.error("Attaching douplicated path to Forest")
        self.sprouts[tree_id].add(sprout_path)

    def attach_tree(
        self, tree: Tree, tree_file: Path, local_id: int
    ) -> ArborealTracker:
        return self._attach(tree, tree_file, local_id=local_id)

    def attach_new_tree(self, model: str, prompt: Prompt) -> ArborealTracker:
        """Create new Tree with initial Sprout"""
        config: SachmisConfig = get_config()

        tree_stem: str = prompt.slug_topic
        new_tree: Tree = Tree.create_with_sprout(
            # TODO: empty prompt or so?
            model=model,
            prompt=prompt,
            tree_stem=tree_stem,
        )
        tree_id: int = self._next_instance_id
        tree_file: Path = config.paths.tree_file(
            id=tree_id, model=model, stem=tree_stem
        )

        # LATER: save as option, delayed? save after successful loading it
        new_tree.save_state(tree_file, lock_required=False)

        return self.attach_tree(
            tree=new_tree, tree_file=tree_file, local_id=tree_id
        )

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Forest - Health checks, maybe -> ArborealDisk?
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    def _prepare_file_registry(self, from_empty_status=False):
        # TODO: synchronize local file manager and upload file manager
        pass
        # if from_empty_status:
        #     logger.info("Dropping local files")
        #     logger.debug(self.files)
        #     self.files: list[UploadFile] = []
        #     return

        # TODO: check online status as well?

    def _prune_local_files(self):
        """Drop files in registry if not in local folder"""

        # logger.info(f"Start pruning files: {self.n_files=}")
        #
        # self.files: list[UploadFile] = [
        #     file  # Assuming flat file structure
        #     for file in self.files
        #     if file.name in self.files_on_disk()
        # ]

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Forest - Custom Functions and Attributes
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    @classmethod
    def with_camp(cls, camp: CampManager) -> Self:
        roles: SstFileRegistry = camp.roles
        files: UploadRegistry = camp.files
        images: SstFileRegistry = camp.images

        return cls(roles=roles, files=files, images=images)

    def provide_camp(self) -> CampManager:
        """Attach registry to new CampManager"""
        return CampManager(
            roles=self.roles, files=self.files, images=self.images
        )

    # TASK: update / sync files with camp manager
    # - distribute at beginning of task
    # - collect at end, handle overlaps

    @property
    def n_files(self) -> int:
        return self.files.n_files

    @property
    def n_images(self) -> int:
        return self.images.n_files
