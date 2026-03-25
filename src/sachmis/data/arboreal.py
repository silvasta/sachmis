import shutil
from datetime import datetime
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, Field

from sachmis.config.manager import config

from .files import Prompt, Response, UploadFile

# NEXT: Global ID strucutre
# - Biome, no id
# - Forest, id from ...
#   - movable inside Biome
# - Tree, id from 1 (probably)
#   - movable inside Biome
# - Sprout, id needed?
#   - Tree -> [Sprout]
#   - Sprout -> [Sprout]


class Sprout(BaseModel):
    """Successor of Tree, can have own successors"""

    id: int  # starting at 1
    prompt: Prompt
    response: Response | None
    sprouts: list["Sprout"] = Field(default_factory=list)

    @property
    def n_sprouts(self) -> int:
        return 1 + sum(sprout.n_sprouts for sprout in self.sprouts)


class Tree(BaseModel):
    """Top element inside Forest: entry point for every conversation"""

    id: int  # starting at 1
    model: str  # model.unique
    tree_stem: str
    sprouts: list[Sprout] = Field(default_factory=list)

    @property
    def n_sprouts(self) -> int:
        return sum(sprout.n_sprouts for sprout in self.sprouts)

    def attach_fresh_sprout(self, prompt: Prompt) -> Sprout:
        """Attach new sprout without response"""

        id: int = self._find_unique_id()
        new_sprout: Sprout = Sprout(id=id, prompt=prompt, response=None)

        self.sprouts.append(new_sprout)
        logger.debug(f"Attached to Tree: {new_sprout=}")

        return new_sprout

    def _find_unique_id(self) -> int:
        # LATER: proper id handling, check ids|new concept
        # e.g. Tree gets pruned or so
        return len(self.sprouts) + 1


class Forest(BaseModel):
    """Master tree file: Data of all Trees and Sprouts in base"""

    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime | None = None
    trees: list[Tree] = Field(default_factory=list)

    files: list[UploadFile] = Field(default_factory=list)
    images: list[Path] = Field(default_factory=list)

    # TASK: file handling
    # - Biome/Forest/Sprout
    # - UploadFile -> xAI/Google-File -> how to save again as 1 file??

    @property
    def n_trees(self) -> int:
        return len(self.trees)

    @property
    def n_sprouts(self) -> int:
        return sum(tree.n_sprouts for tree in self.trees)

    @property
    def n_files(self) -> int:
        return len(self.files)

    @property
    def n_images(self) -> int:
        return len(self.images)

    @property
    def file_names(self) -> set[str]:
        return set(file.name for file in self.files)

    @property
    def files_in_folder(self) -> list[str]:
        # TASK: file providing and filtering
        return [
            file.name
            for file in config.paths.file_dir.glob("*")
            if file.is_file()
        ]

    @classmethod
    def load_state(cls, forest_file: Path | None = None) -> "Forest":
        logger.info("Load Forest from json")

        if forest_file is None:
            forest_file: Path = config.paths.forest_file

        if not forest_file.exists():
            logger.error(f"No forest at target location: {forest_file=}")
            raise AttributeError("Invalid path for Forest!")

        forest: Forest = cls.model_validate_json(forest_file.read_text())

        logger.info(f"Forest loaded with {len(forest.trees)} Trees")
        return forest

    def save_state(self, forest_file: Path | None = None):
        logger.info("Save Forest to json")

        if forest_file is None:
            forest_file: Path = config.paths.biome_file

        self.last_updated: datetime = datetime.now()

        forest_file.write_text(self.model_dump_json())
        logger.info(f"Forest saved with {len(self.trees)} Trees")

    def new_tree(self, model: str, tree_stem: str) -> Tree:
        """Attach new Tree to forest"""

        id: int = self._find_unique_id()
        new_tree: Tree = Tree(id=id, model=model, tree_stem=tree_stem)

        self.trees.append(new_tree)
        logger.debug(f"Attached to Forest: {new_tree=}")

        return new_tree

    def _find_unique_id(self) -> int:
        # LATER: proper id handling, check ids|new concept
        # e.g. Tree gets pruned or so
        return len(self.trees) + 1

    def load_local_files(self, from_empty_status=False):
        """Update file registry with new files placed in folder"""

        self._prepare_file_registry()

        logger.info(f"Start loading files: {self.n_files=}")

        # LATER: sort! by folder/section? check with shmoodle

        logger.info("Confirming local files")
        for filename in self.files_in_folder:
            if filename in self.file_names:  # PERF: set init?
                continue
            self.files.append(UploadFile(name=filename))
            logger.info(f"Added new file: {filename}")

    def file_by_name(self, name: str) -> UploadFile:
        for file in self.files:
            if file.name == name:
                return file
        else:
            raise ValueError(f"File with {name=} not in registry")

    def load_files_from_path(self, files: list[Path]) -> list[UploadFile]:
        confirmed_files: list[UploadFile] = []
        new_loaded_files: list[UploadFile] = []

        for file in files:
            if file.name in self.file_names:
                confirmed_files.append(self.file_by_name(file.name))
                logger.debug(f"Already loaded: {file.name=}")
            else:
                camp_file: Path = config.paths.file_dir / file.name
                shutil.copy(file, camp_file)
                forest_file = UploadFile(name=camp_file.name)
                self.files.append(forest_file)
                new_loaded_files.append(forest_file)
                logger.info(f"Attached to Forest: {file.name=}")

        logger.info(f"Prepared: {new_loaded_files=}")
        confirmed_files += new_loaded_files

        logger.info(f"Total: {confirmed_files=}")
        return confirmed_files

    def _prepare_file_registry(self, from_empty_status=False):
        if from_empty_status:
            logger.info("Dropping local files")
            logger.debug(self.files)
            self.files: list[UploadFile] = []
            return

        # TODO: check online status as well? -> as function of Derived(UploadFile)
        self._prune_local_files()

    def _prune_local_files(self):
        """Drop files in registry if not in local folder"""

        logger.info(f"Start pruning files: {self.n_files=}")

        self.files: list[UploadFile] = [
            file  # Assuming flat file structure
            for file in self.files
            if file.name in self.files_in_folder
        ]


class Biome(BaseModel):
    """Global Master Forest, registry for entire content"""

    forests: list[Path] = Field(default_factory=list)
    # LATER: find better way for tracking moved forests
    outdated_forests: list[Path] = Field(default_factory=list)

    responses: list[Path] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime | None = None

    @property
    def n_forest(self) -> int:
        return len(self.forests)

    @property
    def n_responses(self) -> int:
        return len(self.responses)

    @property
    def role_paths(self) -> list[Path]:
        return list(config.paths.role_dir.glob("*"))

    @property
    def roles(self) -> list[str]:
        return [role.name for role in self.role_paths]

    @property
    def n_roles(self) -> int:
        return len(self.roles)

    # LATER: implement counter but needs first: load_all_forest
    # @property
    # def n_trees(self) -> int:
    #     return sum(forest.n_trees for forest in self.forests)
    # @property
    # def n_sprouts(self) -> int:
    #     return sum(tree.n_sprouts for tree in self.trees)

    @classmethod
    def load_state(cls, biome_file: Path | None = None) -> "Biome":
        logger.info("Load Biome from json")

        if biome_file is None:
            biome_file: Path = config.paths.biome_file

        if not biome_file.exists():
            logger.error(f"No biome at target location: {biome_file=}")
            raise AttributeError("Invalid path for Biome!")

        biome: Biome = cls.model_validate_json(biome_file.read_text())
        logger.info(f"Biome loaded with {biome.n_forest} Forests")

        return biome

    def save_state(self, biome_file: Path | None = None):
        logger.info("Save Biome to json")

        if biome_file is None:
            biome_file: Path = config.paths.biome_file

        self.last_updated: datetime = datetime.now()

        biome_file.write_text(self.model_dump_json())
        logger.info(f"Biome saved with {self.n_forest} Forests")

    def _prune_dublicated_forest_paths(self):

        if len(set(self.forests)) == self.n_forest:
            logger.debug(f"No dublicated forest paths found {self.n_forest=}")
            return

        logger.warning("Found doublicated forest paths!")
        logger.info(f"Before prune: {self.n_forest=}")

        unique_forests: set[Path] = set()
        for path in self.forests:
            if path in unique_forests:
                logger.warning(f"Remove doublicated forest: {path=}")
            else:
                unique_forests.add(path)

        self.forests: list[Path] = list(unique_forests)
        logger.info(f"After prune: {self.n_forest=}")

    def _check_active_forest_paths(self):
        for path in self.forests:
            if not path.exists():
                logger.warning(f"Missing forest: {path=}")
                self.outdated_forests.append(path)
                self.forests.remove(path)

    def attach_new_full_response(self, text: str, path: Path):
        # LATER: somehow processing something?
        path.write_text(text)
        self.responses.append(path)
