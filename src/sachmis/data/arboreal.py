import shutil
from datetime import datetime
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, Field

from sachmis.config import SachmisConfig, get_config
from sachmis.utils.print import printer

from .files import Prompt, Response, UploadFile

config: SachmisConfig = get_config()


class Sprout(BaseModel):
    """Successor of Tree, can have own successors"""

    # NEXT: id, use uuid - assigned by Biome?
    tree_locator: str  # LATER: why include tree id?
    model: str  # LATER: redundant, but fine?
    prompt: Prompt
    response: Response | None
    sprouts: list["Sprout"] = Field(default_factory=list)

    @property
    def n_sprouts(self) -> int:
        return 1 + sum(sprout.n_sprouts for sprout in self.sprouts)

    @property
    def answer_path(self) -> Path:
        """Calculated from CWD, used to save response"""
        return config.paths.answer_file(
            self.prompt.topic, tree_locator=self.tree_locator, model=self.model
        )

    @property
    def write_answer_get_path(self) -> Path:
        if self.response is None:
            raise AttributeError(f"Can't process empty response of {self=}")
        unique_answer_path: Path = self.answer_path
        unique_answer_path.write_text(self.response.content)
        return unique_answer_path


class Tree(BaseModel):
    """Top element inside Forest: entry point for every conversation"""

    id: int  # starting at 1
    model: str  # model.unique
    tree_stem: str
    sprout: Sprout

    @property
    def n_sprouts(self) -> int:
        return self.sprout.n_sprouts

    @classmethod
    def create_with_fresh_sprout(
        cls, id: int, model: str, prompt: Prompt
    ) -> "Tree":
        sprout: Sprout = Sprout(
            tree_locator=f"{id}-1", model=model, prompt=prompt, response=None
        )
        return Tree(id=id, model=model, tree_stem=prompt.topic, sprout=sprout)

    def find_sprout(self, tree_locator: str) -> Sprout:

        tree_id, *sprout_locations = tree_locator.split("-")
        if int(tree_id) != self.id:
            raise AttributeError(f"Got {tree_locator=} for {self.id=}")

        # Start iteration at root sprout, then follow the sprouts
        current_sprout: Sprout = self.sprout

        for next_sprout in sprout_locations:
            next_index: int = int(next_sprout) - 1
            if current_sprout.sprouts:
                current_sprout: Sprout = current_sprout.sprouts[next_index]
            else:  # REMOVE:
                logger.debug(f"ended at {next_sprout=} with {current_sprout=}")

        return current_sprout

    def generate_locator(self, old_tree_locator: str) -> str:
        previous_sprout: Sprout = self.find_sprout(old_tree_locator)
        new_locator_end: int = len(previous_sprout.sprouts) + 1

        return f"{old_tree_locator}-{new_locator_end}"

    def attach_fresh_sprout(
        self, old_tree_locator: str, model: str, prompt: Prompt
    ) -> Sprout:
        logger.debug(f"{old_tree_locator=}")
        new_tree_locator: str = self.generate_locator(old_tree_locator)
        logger.debug(f"{new_tree_locator=}")
        new_sprout: Sprout = Sprout(
            tree_locator=new_tree_locator,
            model=model,
            prompt=prompt,
            response=None,
        )
        logger.debug(f"Attached to Sprout: {new_sprout=}")
        return new_sprout


class Forest(BaseModel):
    """Master tree file: Data of all Trees and Sprouts in base"""

    # NEXT: id
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime | None = None
    trees: list[Tree] = Field(default_factory=list)

    files: list[UploadFile] = Field(default_factory=list)
    images: list[Path] = Field(default_factory=list)

    # NEXT:
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

    def files_on_disk(self) -> list[str]:
        # TASK: provide file with filtering
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
            forest_file: Path = config.paths.forest_file
        logger.debug(f"saved to: {forest_file=}")

        self.last_updated: datetime = datetime.now()

        forest_file.write_text(self.model_dump_json())
        logger.info(f"Forest saved with {len(self.trees)} Trees")

    @property
    def tree_ids(self) -> set[int]:
        return set(tree.id for tree in self.trees)

    def has_tree_with_id(self, id: int):
        return True if id in self.tree_ids else False

    def _find_unique_id(self) -> int:
        id: int = max(1, len(self.trees))
        while self.has_tree_with_id(id):
            id += 1
        return id

    def attach_new_tree(self, model: str, prompt: Prompt) -> Tree:
        id: int = self._find_unique_id()
        tree: Tree = Tree.create_with_fresh_sprout(
            id=id, model=model, prompt=prompt
        )
        self.trees.append(tree)
        logger.debug(f"Attached to Forest: {tree=}")

        return tree

    def attach_sprout_in_tree(
        self, tree_locator: str, model: str, prompt: Prompt
    ):
        tree_id: str = tree_locator.split("-")[0]
        logger.debug(f"{tree_id=}")
        tree: Tree = self.find_tree_by_id(int(tree_id))

        if tree.model != model:
            msg = f"Invalid match! {id=} but {model=} must match: {tree=} "
            raise ValueError(msg)

        return tree.attach_fresh_sprout(
            old_tree_locator=tree_locator, model=model, prompt=prompt
        )

    def find_sprout_in_tree(self, tree_locator: str) -> Sprout:
        tree_id: str = tree_locator.split("-")[0]
        logger.debug(f"{tree_id=}")
        tree: Tree = self.find_tree_by_id(int(tree_id))
        # REFACTOR: together with attach
        return tree.find_sprout(tree_locator)

    def find_tree_by_id(self, tree_id: int) -> Tree:
        for tree in self.trees:
            if tree.id == tree_id:
                logger.debug(f"Found tree with {id=}")
                return tree
        else:
            raise ValueError(f"{tree_id=} not found, use 0 for new tree")

    def load_local_files(
        self,
        local_file_dir: Path | None = None,
        from_empty_status=False,
    ):
        """Update file registry with new files placed in folder"""
        # LATER: sort! by folder/section? check with shmoodle

        self._prepare_file_registry(from_empty_status)
        logger.info(f"Start loading files: {self.n_files=}")

        target_dir: Path = config.paths.file_dir
        local_file_dir: Path = local_file_dir or target_dir
        # TODO: what else when local==target?

        new_files: list[str] = [
            file.name
            for file in local_file_dir.glob("*")
            if file.is_file()
            # TODO: check for dublicated, especially from camp
        ]

        # NEXT: split in:
        # - load or update from .camp/files
        # - load from other folder (or recive directly list with paths)
        # Move files from local_file_dir to target_dir

        result: list[UploadFile] = []

        for file in new_files:
            if file in self.file_names:
                msg = f"Dublicated name for: {file=}, implement hash or compare size?"
                logger.warning(msg)
                continue
            # TODO: global_path: Path = PathGuard.unique(Path(file))
            # - slugify name, but store original
            # check with shmoodle
            new_file = UploadFile(local_path=Path(file))
            self.files.append(new_file)
            result.append(new_file)
            logger.info(f"Added {new_file=}")

        printer.lines_from_list(
            lines=[r.description for r in result],
            header=f"New loaded files {len(result)}",
            title=f"{local_file_dir}",
        )

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
            if file.name in self.files_on_disk()
        ]


class Biome(BaseModel):
    """Global Master Forest, registry for entire content"""

    # LATER: id for forest?
    forests: list[Path] = Field(default_factory=list)
    # LATER: find better way for tracking moved forests
    outdated_forests: list[Path] = Field(default_factory=list)

    # LATER: use list[SstFile] for that?
    responses: list[Path] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.now)
    # updated_at?
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

    # TODO: inactive roles + move function

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
        # - link full response to response, Path to Sprout.response?
        path.write_text(text)
        self.responses.append(path)

    def attach_new_forest(self, forest_file: Path) -> Forest:

        # LATER: ? id: int = self._find_unique_id()
        new_forest = Forest()
        new_forest.save_state(forest_file)

        self.forests.append(forest_file)
        logger.debug(f"Attached to Biome: {new_forest=}")

        return new_forest
