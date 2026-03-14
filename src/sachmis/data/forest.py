from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, Field


# REFACTOR: new file handling, group by chat and forest
# - create database (can be json) at central location
# - write to file system only on request
class Tree(BaseModel):
    """Tree with id and file data for 1 prompt/answer pair
    evolves to nested folder root when selected to sprout"""

    id: str  # from response, most important value
    model: str  # model.unique
    created_at: datetime = Field(default_factory=datetime.now)
    tree_stem: str  # name, created from topic
    ancestor: str = ""  # "" for top folder (multiple roots possible)
    full_response_path: Path | None  # backup path with all files
    usage: dict[str, int] = Field(default_factory=dict)
    # TASK: files! (and images)
    # TASK: save dialog
    content: str | None = None  # for big loops without file system tree or forest


class File(BaseModel):
    """Local file for upload and usage in prompt"""

    # NEXT: base in silvasta, derive here for sachmis,
    # derive further for xai,google?
    name: str
    category: str
    topic: str
    local_path: Path  # relative from local filedir (.camp/files)
    # from xAI upload, needed for prompt attach
    x_id: str | None = None
    # from Goole upload, needed for prompt attach
    g_uri: str | None = None
    g_mime_type: str | None = None

    @property
    def description(self):
        return f"[blue]{self.category}[/]-[green]{self.topic}[/]-[white]{self.local_path.name}[/]"


class Forest(BaseModel):
    """Top folder file with data of all trees and subtrees"""

    # REFACTOR: new concept

    tree_file_path: Path  # the master tree file (stands and falls with the base)
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime | None = None
    # the family tree of roots of sprouts from trees in forest
    trees: dict[str, Tree] = Field(default_factory=dict)
    # supporting documents
    # TASK: file status, outdated etc, store history
    files: list[File] = Field(default_factory=list)

    @property
    def file_categories(self) -> list[str]:
        return list(set(file.category for file in self.files))

    @property
    def file_topics(self) -> list[str]:
        return list(set(file.topic for file in self.files))

    @property
    def file_paths(self) -> list[Path]:
        return list(set(file.local_path for file in self.files))

    def file_selection(
        self, categories: list[str] | None = None, topics: list[str] | None = None
    ) -> list[File]:
        """Select subset of both (or all files) and intersect the selections"""

        if not categories:  # catch None and [], fail if categories = 0
            categories: list[str] = self.file_categories
        if not topics:
            topics: list[str] = self.file_topics

        selection: list[File] = [
            file
            for file in self.files
            # TODO: and | or for selection params
            if file.category in categories and file.topic in topics
        ]

        logger.info(f"Total {len(selection)=}")
        return selection

    def save_state(self):
        """Save everything to json"""
        self.last_updated: datetime = datetime.now()
        self.tree_file_path.write_text(
            self.model_dump_json(indent=4, by_alias=True),
        )
        logger.info(f"Forest saved with {len(self.trees)} Trees")

    @classmethod
    def load_state(cls, tree_file_path: Path) -> "Forest":
        """Reconstruct the Trees and build the Forest"""
        logger.info("Load Forest from json")

        if not tree_file_path.exists():
            logger.error("No tree file at given path!")
            raise AttributeError(f"Invalid {tree_file_path=}")

        forest: "Forest" = cls.model_validate_json(tree_file_path.read_text())
        logger.info(f"Forest loaded with {len(forest.trees)} Trees")

        return forest

    def update_files(self, file_dir, sort_method: str, from_empty_status=False):
        """Update base file registry with new files placed in folder, or empty current list first"""
        if from_empty_status:
            self.files: list[File] = []

        # WARN: remove unused files, check here if all files still avaliable
        already_added: set[Path] = set(file.local_path for file in self.files)
        print(already_added)

        logger.info("Start adding files")
        logger.info(f"{sort_method=}")

        for path in file_dir.rglob("*"):
            if not path.is_file():
                logger.debug(f"No file at: {path=}")
                continue

            local_path: Path = path.relative_to(file_dir)
            if local_path in already_added:
                logger.debug(f"Path already_added: {local_path=}")
                continue

            match sort_method:
                case "simple":
                    name: str = local_path.name
                    topic: str = "General"
                    category: str = "General"
                case "folder_cat":  # INFO: RODYN, gtc
                    name: str = local_path.name
                    category: str = (
                        local_path.parent.name
                        if local_path.parent != Path(".")
                        else "General"
                    )
                    splitted: list[str] = (  # stem?
                        local_path.name.strip(".pdf").strip(".tex").split("-")
                    )
                    # topic: str = splitted[1]   if category == "Lecture" else "General" # INFO: rodyn
                    concat_from: int = 0 if category == "Tex" else 1  # INFO: gtc
                    topic: str = "-".join(splitted[concat_from:])
                case "folder_topic":  # INFO: rodyn
                    name: str = local_path.name
                    topic: str = local_path.parent.name
                    category: str = (
                        "Exercise"
                        if ("exercise" in name or "solution" in name)
                        else "General"
                    )
                case "section":  # INFO: mpc
                    splitted: list[str] = local_path.name.split("_")
                    name: str = "-".join(splitted[1:]).strip(".pdf")
                    topic: str = splitted[0]
                    category: str = (
                        "Exercise"
                        if ("exercise" in name or "solution" in name)
                        else "General"
                    )
                case _:
                    logger.error(f"Unknown {sort_method=}: files ignored")
                    break

            self.files.append(
                File(name=name, category=category, topic=topic, local_path=local_path)
            )
            logger.info(f"Added new file: {local_path}")

    def find_tree_by_path(self, sprout_path: Path) -> Tree | None:
        # WARNING: so far only with relative path in local folder (=file.stem)
        sprout_stem: str = sprout_path.stem
        for tree in self.trees.values():
            if tree.tree_stem == sprout_stem:
                return tree
        return None

    def find_local_root_tree(
        self,
        local_path: Path | None = None,
    ) -> Tree | None:
        """Find root Tree of the current location in subfolders,
        top folder has no root Tree -> None"""

        local_path: Path = local_path or Path.cwd()
        logger.debug(f"{local_path=}")

        if local_path == self.tree_file_path.parent:
            logger.debug("Located in root directory, returning None")
            return None

        candidates: list[Tree] = []
        # FIX: better method, dublicates exist...
        lookup_stem: str = str(local_path).split("/")[-1]
        logger.debug(f"{lookup_stem=}")

        for tree in self.trees.values():
            if tree.tree_stem == lookup_stem:
                logger.debug("found tree in cwd:", tree.tree_stem)
                candidates.append(tree)

        match len(candidates):
            case 0:
                logger.error("No local tree in Forest!")
                raise FileNotFoundError("No match found of tree_stem with local_path")
            case 1:
                logger.debug("found 1 root")
                final_tree: Tree = candidates[0]
                return final_tree
            case _:
                # NOTE: later on multiple selections should be possible,
                # - f.e. last tree in flat/folder structure
                logger.info(f"Processing {len(candidates)} trees")
                logger.debug(f"processing {candidates=} trees")
                # INFO: just return the newest
                return max(candidates, key=lambda tree: tree.created_at)


@contextmanager
# NEXT: something like this!
def loaded_forest(path: Path):
    logger.debug("loading forest")
    try:
        forest: Forest = Forest.load_state(path)
        logger.debug("yielding forest")
        yield forest
    finally:
        forest.save_state()
        logger.debug("finally context ended")
