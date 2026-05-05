from pathlib import Path
from typing import Literal

from loguru import logger
from sstcore import PathGuard
from sstcore.config import SstPaths
from sstcore.utils.path import (
    recursive_parent,
    recursive_root,
)

from ..exceptions import (
    ArborealFileExistsError,
    NotInCampError,
    NotInForestError,
)
from .defaults import Defaults
from .names import Names


class Paths(SstPaths[Names, Defaults]):
    """Assemble paths for project"""

    @property
    def biome_dir(self) -> Path:
        return self.data_home

    @property
    @PathGuard.file(raise_error=True)
    def biome_file(self) -> Path:
        """Current active Biome file"""
        return self._biome_file()

    @property
    def active_biome(self) -> bool:
        return self.unconfirmed_biome_file.exists()

    @property
    def unconfirmed_biome_file(self) -> Path:
        """unchecked composition of path and name"""
        return self._biome_file()

    def _biome_file(self, biome_filename: str | None = None) -> Path:
        """path constructor class"""
        return self.biome_dir / (biome_filename or self._names.biome_file)

    def new_biome_file(self, name: str) -> Path:
        """Generate new biome_file path if it not already exists"""

        # Ensure it works for 'name.json' or just 'name'
        biome_filename: str = f"{name.strip('.json')}.json"

        new_file: Path = self._biome_file(biome_filename)

        if new_file in self.biome_files:
            raise ArborealFileExistsError("Biome", new_file)

        logger.success(f"Created writable Path for new Biome: {new_file=}")

        return new_file

    @property
    def biome_files(self) -> set[Path]:
        # LATER: ensure no other .json in biome_dir
        return set(self.biome_dir.glob("*.json"))

    @property
    def base_dir(self) -> Path:
        root: Path | None = recursive_root(
            path=Path.cwd(), indicator=self._names.camp_dir
        )
        if root is None:
            raise NotInForestError
        return root

    @property
    def in_forest(self) -> bool:
        try:
            _ = self.base_dir
            return True
        except NotInForestError:
            return False

    @property
    @PathGuard.dir
    def camp_dir(self) -> Path:
        return self.base_dir / self._names.camp_dir

    @property
    def camp_dir_as_parent(self):
        parent: Path | None = recursive_parent(
            path=Path.cwd(), parent_dir_name=self._names.camp_dir
        )
        if parent is None:
            raise NotInCampError
        return parent

    @property
    def in_camp(self) -> bool:
        try:
            _ = self.camp_dir_as_parent
            return True
        except NotInCampError:
            return False

    @property
    def forest_file(self) -> Path:
        """Error if not in base"""
        return self.camp_dir / self._names.forest_file

    @property
    @PathGuard.dir
    def tree_dir(self) -> Path:
        """Error if not in base"""
        return self.camp_dir / self._names.tree_dir

    @PathGuard.unique(ensure_parent=True)
    def tree_file(self, id: int, model: str, stem: str) -> Path:
        """Error if not in base"""
        tree_file: str = self._names.tree_file([id, model, stem])
        return self.tree_dir / tree_file

    @property
    @PathGuard.dir
    def file_dir(self):
        return self.camp_dir / self._names.file_dir

    @property
    def local_file_dir(self):
        """Used for loading files automatically"""
        return Path.cwd() / self._names.file_dir

    @property
    @PathGuard.dir
    def image_dir(self):
        return self.camp_dir / self._names.image_dir

    @property
    def local_image_dir(self):
        """Used for loading images automatically"""
        return Path.cwd() / self._names.file_dir

    @property
    @PathGuard.dir
    def role_dir(self) -> Path:
        return self.data_home / self._names.role_dir.lower()

    def role_paths(
        self, mode: Literal["all", "local", "global"] = "all"
    ) -> list[Path]:
        return [
            # FIX: works  that now?
            *(self.role_dir.glob("*") if mode == "all" or "global" else []),
            *(
                self.camp_role_dir.glob("*")
                if mode == "all" or "local"
                else []
            ),
        ]

    @property
    @PathGuard.dir
    def camp_role_dir(self) -> Path:
        return self.camp_dir / self._names.role_dir

    @property
    @PathGuard.dir
    def inactive_role_dir(self) -> Path:
        return self.role_dir.with_stem(f"inactive-{self.role_dir.stem}")

    def inactive_role_paths(
        self, mode: Literal["all", "local", "global"] = "all"
    ) -> list[Path]:
        i_camp_role_dir: Path = self.inactive_camp_role_dir
        return [
            *(self.inactive_role_dir.glob("*") if mode == "global" else []),
            *(i_camp_role_dir.glob("*") if mode == "local" else []),
        ]

    @property
    @PathGuard.dir
    def inactive_camp_role_dir(self) -> Path:
        return self.role_dir.with_stem(f"inactive-{self.camp_role_dir.stem}")

    @property
    @PathGuard.dir
    def full_response_dir(self) -> Path:
        return self.state_home / self._names.response_dir

    @PathGuard.unique
    def full_response(self, topic: str, model: str, suffix=".txt") -> Path:
        # NOTE: better locator?
        stem: str = self._names.sprout_stem.computed(
            topic=topic, locator="B", spec=model
        )
        return self._path_from_stem(stem, suffix, self.full_response_dir)

    @PathGuard.unique(ensure_parent=True)
    def prompt_file(
        self,
        topic: str,
        locator: str,
        root_dir: Path | None = None,
        suffix: str = ".md",
    ) -> Path:
        """New prompt file name after usage and move"""
        prompt_stem: str = self._names.sprout_stem.computed(
            locator=locator, spec="prompt", topic=topic
        )
        return self._path_from_stem(prompt_stem, suffix, root_dir)

    def _path_from_stem(
        self, stem: str, suffix: str, root_dir: Path | None = None
    ) -> Path:
        suffix: str = suffix if suffix.startswith(".") else f".{suffix}"
        return (root_dir or Path.cwd()) / f"{stem}{suffix}"

    @PathGuard.unique(ensure_parent=True)
    def answer_file(
        self,
        topic: str,
        locator: str,
        model: str,
        suffix=".md",
        root_dir: Path | None = None,
    ) -> Path:
        answer_stem: str = self._names.sprout_stem.computed(
            locator=locator, spec=model, topic=topic
        )
        return self._path_from_stem(answer_stem, suffix, root_dir)
