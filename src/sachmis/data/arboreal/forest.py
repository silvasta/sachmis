from pathlib import Path
from typing import Self

from sstcore.data import SstFileRegistry

from ...config import SachmisConfig, get_config
from ..conversation.prompt import Prompt
from ..files import CampManager, UploadRegistry
from .base import Arboreal, ArborealTracker
from .tree import Tree


class Forest(Arboreal[Tree]):
    """Master Tree File: Data of all Trees and Sprouts in Base"""

    files: UploadRegistry
    images: SstFileRegistry
    roles: SstFileRegistry

    @property
    def n_files(self) -> int:
        return self.files.n_files

    @property
    def n_images(self) -> int:
        return self.images.n_files

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Forest - Custom Functions and Attributes
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    @classmethod
    def with_camp(cls, camp: CampManager) -> Self:
        # REFACTOR: camp here?
        roles: SstFileRegistry = camp.roles
        files: UploadRegistry = camp.files
        images: SstFileRegistry = camp.images

        return cls(roles=roles, files=files, images=images)

    def provide_camp(self) -> CampManager:
        """Attach registry to new CampManager"""
        # REFACTOR: camp here?
        return CampManager(
            roles=self.roles, files=self.files, images=self.images
        )

    # TASK: update / sync files with camp manager
    # - distribute at beginning of task
    # - collect at end, handle overlaps

    # NEXT: call this with ID!

    # def provide_tree(self, previous_sprout: Path) -> ArborealTracker:
    #     for tree_id, paths in self.sprouts.items():
    #         if previous_sprout in paths:
    #             if tracker := self.find_tree_by_unique_id(tree_id):
    #                 return tracker
    #     logger.error(f"{previous_sprout=}")
    #     logger.error(self.sprouts)
    #     raise ArborealRegistryMissingError("Forest", "Tree", "MISSING")

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Arboreal - Access to Members
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    @property
    def n_trees(self) -> int:
        """Calculated by num trackers"""
        return self.registry.n_trackers

    @property
    def trees(self) -> list[ArborealTracker]:
        """Serialized part of registry with UUID and ArborealTracker"""
        return self.registry.all_trackers

    @property
    def missing_trees(self) -> list[ArborealTracker]:
        return self.registry.tracker_with_invalid_paths()

    # TODO:
    # def n_sprouts(self) -> int:
    #     return sum(tree.n_sprouts for tree in self.loaded_trees)

    def find_tree_by_local_id(self, id: int) -> ArborealTracker | None:
        return self.registry.find_tracker_by_local_id(id)

    def attach_new_tree(self, prompt: Prompt, save=True) -> ArborealTracker:
        """Create new Tree with initial Sprout"""
        config: SachmisConfig = get_config()

        tree_file: Path = config.paths.tree_file(
            id=(tree_id := self._next_instance_id()),
            stem=(tree_stem := prompt.slug_topic),
        )
        new_tree: Tree = self._setup_tree(prompt, tree_stem)

        if save:
            new_tree.save_state(tree_file, lock_required=False)

        return self.attach_tree(
            tree=new_tree, tree_file=tree_file, local_id=tree_id
        )

    def _setup_tree(self, prompt: Prompt, tree_stem: str) -> Tree:

        new_tree: Tree = Tree.create(prompt=prompt, tree_stem=tree_stem)
        return new_tree

    def attach_tree(
        self, tree: Tree, tree_file: Path, local_id: int
    ) -> ArborealTracker:

        return self.registry.attach(
            arbo=tree, path=tree_file, local_id=local_id
        )

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Forest - Health checks, maybe -> ArborealDisk?
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    # REMOVE:

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
