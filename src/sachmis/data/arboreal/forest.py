from pathlib import Path
from typing import Self

from loguru import logger
from sstcore.data import FileRegistry, SstFileRegistry

from ...config import SachmisConfig, get_config
from ...exceptions import ArborealRegistryMissingError
from ...utils import printer
from ..conversation.prompt import PromptData
from ..files import CampManager, RoleRegistry, UploadRegistry
from .base import Arboreal, ArborealTracker
from .tree import Tree


class Forest(Arboreal[Tree]):
    """Master Tree File: Data of all Trees and Sprouts in Base"""

    roles: RoleRegistry
    files: UploadRegistry
    images: SstFileRegistry

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
    def with_camp(
        cls, path: Path, local_id, camp: CampManager | None = None
    ) -> Self:
        camp: CampManager = camp or CampManager()
        return cls.with_tracker(
            path=path,
            local_id=local_id,
            roles=camp.roles,
            files=camp.files,
            images=camp.images,
        )

    def get_camp(self) -> CampManager:
        """Attach registry to new CampManager"""
        return CampManager(
            roles=self.roles, files=self.files, images=self.images
        )

    def attach_camp_back_by_mirror(self, camp: CampManager):
        """Simply Mirror the changes since Extraction"""

        self._attach_back(self.roles, camp.roles)
        self._attach_back(self.files, camp.files)
        self._attach_back(self.images, camp.images)

    @staticmethod
    def _attach_back[RegistryT: FileRegistry](
        forest: RegistryT, camp: RegistryT
    ):
        """Mirror, Log and Print"""  # TODO: update status
        new: list = forest.mirror_from_registry(external_registry=camp)
        name: str = camp.__class__.__name__
        printer.lines(header=f"New Files from {name} to Forest", lines=new)
        logger.info(f"loaded {len(new)} Files from Camp {name} to Forest")

    def provide_tree(
        self, tree_id: int, raw_prompt: PromptData
    ) -> ArborealTracker:

        # LATER: attach to temp registry, confirm when task went well
        if tree_id == 0:
            return self.attach_new_tree(raw_prompt)
        if tree := self.find_tree_by_local_id(tree_id):
            return tree

        raise ArborealRegistryMissingError("Forest", "Tree", f"{tree_id=}")

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

    def attach_new_tree(self, prompt: PromptData) -> ArborealTracker:
        """Create new Tree with initial Sprout"""
        config: SachmisConfig = get_config()

        tree_file: Path = config.paths.tree_file(
            id=(tree_id := self._next_instance_id()), stem=prompt.slug_topic
        )
        new_tree: Tree = self._setup_tree(prompt, tree_file, local_id=tree_id)
        new_tree.save_state(tree_file, lock_required=False)

        return self.attach_tree(
            tree=new_tree, tree_file=tree_file, local_id=tree_id
        )

    def _setup_tree(
        self, prompt: PromptData, tree_file: Path, local_id: int
    ) -> Tree:
        return Tree.with_prompt(
            prompt=prompt, tree_file=tree_file, local_id=local_id
        )

    def attach_tree(
        self, tree: Tree, tree_file: Path, local_id: int
    ) -> ArborealTracker:

        return self.registry.attach(
            arboreal=tree, path=tree_file, local_id=local_id
        )

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Forest - Health checks, maybe -> ArborealDisk?
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    # REMOVE: or adapt in CampManager

    def _prepare_file_registry(self, from_empty_status=False):
        # TODO: synchronize local file manager and upload file manager
        pass
        # if from_empty_status:
        #     logger.info("Dropping local files")
        #     logger.debug(self.files)
        #     self.files: list[UploadFile] = []
        #     return

        # TODO: check online status as well?

    # REMOVE: or adapt in CampManager
    def _prune_local_files(self):
        """Drop files in registry if not in local folder"""

        # logger.info(f"Start pruning files: {self.n_files=}")
        #
        # self.files: list[UploadFile] = [
        #     file  # Assuming flat file structure
        #     for file in self.files
        #     if file.name in self.files_on_disk()
        # ]
