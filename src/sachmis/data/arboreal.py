from datetime import datetime
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, Field

from sachmis.config.manager import config

from .files import Prompt, Response


class Sprout(BaseModel):
    """Successor of Tree, can have own successors"""

    model: str  # model.unique
    prompt: Prompt
    response: Response
    sprouts: list["Sprout"] = Field(default_factory=list)


class Tree(BaseModel):
    """Top element inside Forest: entry point for every conversation"""

    tree_stem: str
    sprouts: list[Sprout] = Field(default_factory=list)


class Forest(BaseModel):
    """Master tree file: Data of all Trees and Sprouts in base"""

    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime | None = None
    trees: list[Tree] = Field(default_factory=list)

    files: list[Path] = Field(default_factory=list)  # TODO: file management
    images: list[Path] = Field(default_factory=list)  # TODO: file management

    # TASK: file status, outdated etc, store history
    # - maybe path? easier for biome or creation or context
    # TODO: properties like: n_trees, n_sprouts etc

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

    # TASK: file handling, Biome/Forest/Sprout
    # def update_files(
    #     self, file_dir, sort_method: str, from_empty_status=False
    # ):
    #     """Update base file registry with new files placed in folder, or empty current list first"""
    #     if from_empty_status:
    #         self.files: list[File] = []
    #
    #     # WARN: remove unused files, check here if all files still avaliable
    #     already_added: set[Path] = set(file.local_path for file in self.files)
    #     print(already_added)
    #
    #     logger.info("Start adding files")
    #     logger.info(f"{sort_method=}")
    #
    #     for path in file_dir.rglob("*"):
    #         if not path.is_file():
    #             logger.debug(f"No file at: {path=}")
    #             continue
    #
    #         local_path: Path = path.relative_to(file_dir)
    #         if local_path in already_added:
    #             logger.debug(f"Path already_added: {local_path=}")
    #             continue
    #
    #         match sort_method:
    #             case "simple":
    #                 name: str = local_path.name
    #                 topic: str = "General"
    #                 category: str = "General"
    #             case "folder_cat":  # INFO: RODYN, gtc
    #                 name: str = local_path.name
    #                 category: str = (
    #                     local_path.parent.name
    #                     if local_path.parent != Path(".")
    #                     else "General"
    #                 )
    #                 splitted: list[str] = (  # stem?
    #                     local_path.name.strip(".pdf").strip(".tex").split("-")
    #                 )
    #                 # topic: str = splitted[1]   if category == "Lecture" else "General" # INFO: rodyn
    #                 concat_from: int = (
    #                     0 if category == "Tex" else 1
    #                 )  # INFO: gtc
    #                 topic: str = "-".join(splitted[concat_from:])
    #             case "folder_topic":  # INFO: rodyn
    #                 name: str = local_path.name
    #                 topic: str = local_path.parent.name
    #                 category: str = (
    #                     "Exercise"
    #                     if ("exercise" in name or "solution" in name)
    #                     else "General"
    #                 )
    #             case "section":  # INFO: mpc
    #                 splitted: list[str] = local_path.name.split("_")
    #                 name: str = "-".join(splitted[1:]).strip(".pdf")
    #                 topic: str = splitted[0]
    #                 category: str = (
    #                     "Exercise"
    #                     if ("exercise" in name or "solution" in name)
    #                     else "General"
    #                 )
    #             case _:
    #                 logger.error(f"Unknown {sort_method=}: files ignored")
    #                 break
    #
    #         self.files.append(
    #             File(
    #                 name=name,
    #                 category=category,
    #                 topic=topic,
    #                 local_path=local_path,
    #             )
    #         )
    #         logger.info(f"Added new file: {local_path}")

    # TASK: altough different concept now...
    # - still need to find root(forest_file) and active tree
    # - find best matching for filesystem/global tasks
    #
    # def find_local_root_tree(
    #     self,
    #     local_path: Path | None = None,
    # ) -> Tree | None:
    #     """Find root Tree of the current location in subfolders,
    #     top folder has no root Tree -> None"""
    #
    #     local_path: Path = local_path or Path.cwd()
    #     logger.debug(f"{local_path=}")
    #
    #     if local_path == self.tree_file_path.parent:
    #         logger.debug("Located in root directory, returning None")
    #         return None
    #
    #     candidates: list[Tree] = []
    #     # FIX: better method, dublicates exist...
    #     lookup_stem: str = str(local_path).split("/")[-1]
    #     logger.debug(f"{lookup_stem=}")
    #
    #     for tree in self.trees.values():
    #         if tree.tree_stem == lookup_stem:
    #             logger.debug("found tree in cwd:", tree.tree_stem)
    #             candidates.append(tree)
    #
    #     match len(candidates):
    #         case 0:
    #             logger.error("No local tree in Forest!")
    #             raise FileNotFoundError(
    #                 "No match found of tree_stem with local_path"
    #             )
    #         case 1:
    #             logger.debug("found 1 root")
    #             final_tree: Tree = candidates[0]
    #             return final_tree
    #         case _:
    #             # NOTE: later on multiple selections should be possible,
    #             # - f.e. last tree in flat/folder structure
    #             logger.info(f"Processing {len(candidates)} trees")
    #             logger.debug(f"processing {candidates=} trees")
    #             # INFO: just return the newest
    #             return max(candidates, key=lambda tree: tree.created_at)


class Biome(BaseModel):
    """Global Master Forest, registry for entire content"""

    forests: list[Path] = Field(default_factory=list)

    # LATER: find better way for tracking moved forests
    outdated_forests: list[Path] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime | None = None

    # TASK: save and load global files!
    # - full response
    # - roles

    @property
    def n_forest(self) -> int:
        return len(self.forests)

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
