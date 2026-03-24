from datetime import datetime
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, Field

from sachmis.config.manager import config

from .files import Prompt, Response, UploadFile


class Sprout(BaseModel):
    """Successor of Tree, can have own successors"""

    model: str  # model.unique # MOVE: to Tree?
    prompt: Prompt
    response: Response
    sprouts: list["Sprout"] = Field(default_factory=list)

    @property
    def n_sprouts(self) -> int:
        return 1 + sum(sprout.n_sprouts for sprout in self.sprouts)


class Tree(BaseModel):
    """Top element inside Forest: entry point for every conversation"""

    tree_stem: str
    sprouts: list[Sprout] = Field(default_factory=list)

    @property
    def n_sprouts(self) -> int:
        return sum(sprout.n_sprouts for sprout in self.sprouts)


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

    def load_local_files(
        self,
        file_dir: Path | None = None,
        from_empty_status=False,
    ):
        """Update file registry with new files placed in folder"""

        if file_dir is None:
            file_dir: Path = config.paths.file_dir

        # Used in confirming local files
        self._local_folder_files: list[str] = [
            # TODO: make this own function, grab folders
            file.name  # INFO: assuming flat file structure in .camp/files/*
            for file in file_dir.glob("*")
            if file.is_file()
        ]

        if from_empty_status:
            logger.info("Dropping local files")
            logger.debug(self.files)
            self.files: list[UploadFile] = []
        else:
            logger.info("Confirming local files")
            self._prune_local_files()
            # TODO: check online status as well?
            # -> as function of Derived(UploadFile)

        logger.info(f"Start loading files: {self.n_files=}")
        forest_files: set[str] = set(file.name for file in self.files)

        # LATER: sort! by folder/section? check with shmoodle

        for filename in self._local_folder_files:
            if filename in forest_files:
                continue
            self.files.append(UploadFile(name=filename))
            logger.info(f"Added new file: {filename}")

    def _prune_local_files(self):
        """Assuming flat file structure/no dublicates in .camp/files/*"""

        logger.info(f"Start pruning files: {self.n_files=}")

        self.files: list[UploadFile] = [
            file
            for file in self.files
            if file.name in self._local_folder_files
        ]


class Biome(BaseModel):
    """Global Master Forest, registry for entire content"""

    forests: list[Path] = Field(default_factory=list)
    # LATER: find better way for tracking moved forests
    outdated_forests: list[Path] = Field(default_factory=list)

    # TODO: link forest and responses
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
