from pathlib import Path

from pydantic import Field

from sachmis.config import SachmisConfig, get_config

from ..files import Prompt, UploadFile
from .base import ArborealDisk, ArborealTracker
from .tree import Tree


class Forest(ArborealDisk[Tree]):
    """Master tree file: Data of all Trees and Sprouts in base"""

    files: list[UploadFile] = Field(default_factory=list)
    images: list[Path] = Field(default_factory=list)  # LATER: SstFile

    # TASK: file management splitted to Upload/Local/Image/... download?
    # - Forest has overview and holds status of files with tracker
    # - Uploader already exists, not neccesarily needed here but maybe nice, 1 call to synchronize remote before big pipelines
    # - CampManager with all local stuff, move files etc, create generalized in Silvasta.data, maybe override in Sachmis.data
    #   - beside pdf and image upload, check as well audio/video etc

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
        return self._registry.all_trackers

    @property
    def loaded_trees(self) -> list[Tree]:
        return self._registry.all_members

    @property
    def missing_trees(self) -> list[ArborealTracker]:
        return self._registry.tracker_with_invalid_paths

    def n_sprouts(self) -> int:
        return sum(tree.n_sprouts for tree in self.loaded_trees)

    @property
    def local_tree_ids(self) -> list[int]:
        return [t.local_id for t in self._registry.all_trackers]

    @property
    def unique_tree_ids(self) -> list[str]:
        return [t.unique_id for t in self._registry.all_trackers]

    def find_tree_by_unique_id(self, id: str) -> Tree | None:
        return self._registry.find_member(id)

    # TODO: Tree or Tracker?

    def find_tree_by_local_id(self, id: str) -> ArborealTracker | None:
        return self._registry.find_tracker_by_local_id(id)

    def attach_tree(
        self, tree: Tree, tree_file: Path, local_id: int
    ) -> ArborealTracker:
        return self._attach(tree, tree_file, local_id=local_id)

    def attach_new_tree(self, model: str, prompt: Prompt) -> Tree:
        """Create new Tree with initial Sprout"""
        config: SachmisConfig = get_config()

        tree_stem: str = prompt.topic
        new_tree: Tree = Tree.create_with_sprout(
            model=model, prompt=prompt, tree_stem=tree_stem
        )
        tree_id: int = self._next_instance_id
        tree_file: Path = config.paths.tree_file(id=tree_id, stem=tree_stem)

        new_tree.save_state(tree_file)
        self.attach_tree(tree=new_tree, tree_file=tree_file, local_id=tree_id)

        return new_tree

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
    ### -- Forest - Custom Functions and Atributes
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    @property
    def n_files(self) -> int:
        return len(self.files)

    @property
    def n_images(self) -> int:
        return len(self.images)
