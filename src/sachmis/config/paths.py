from contextlib import suppress
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
    @PathGuard.dir
    def config_home(self) -> Path:
        # FIX: find new solution!!!
        # FIX: find new solution!!!
        return self.project_root

    @property
    def active_biome(self) -> bool:
        return self.unconfirmed_biome_file.exists()

    @property
    def biome_dir(self) -> Path:
        return self.data_home

    @property
    @PathGuard.file(raise_error=True)
    def biome_file(self) -> Path:
        """Current active Biome file"""
        return self._biome_file()

    def _biome_file(self, biome_filename: str | None = None) -> Path:
        """path constructor class"""
        return self.biome_dir / (biome_filename or self._names.biome_file)

    @property
    def unconfirmed_biome_file(self) -> Path:
        """unchecked composition of path and name"""
        return self._biome_file()

    @property
    def biome_files(self) -> set[Path]:
        # LATER: ensure better, track state
        return set(self.biome_dir.glob("*.json"))

    @property
    def num_biome_files(self) -> int:
        return len(self.biome_files)

    def new_biome_file(self, name: str) -> Path:
        """Generate new biome_file path if it not already exists"""

        biome_filename: str = f"{name.strip('.json')}.json"
        new_biome_file: Path = self._biome_file(biome_filename)

        if new_biome_file in self.biome_files:
            raise ArborealFileExistsError("Biome", new_biome_file)

        logger.success(f"Created Path for new Biome: {new_biome_file=}")

        return new_biome_file

    @property
    def base_dir(self) -> Path:
        root: Path | None = recursive_root(
            path=Path.cwd(), indicator=self._names.camp_dir
        )
        if root is None:
            raise NotInForestError
        return root

    def cwd_to_base_dir(self, strict=True) -> Path:
        """Error for outside Forest, try with strict=False for ../../path"""
        return PathGuard.relative(
            target=Path.cwd(), root=self.base_dir, strict=strict
        )

    @property
    def in_forest(self) -> bool:
        with suppress(NotInForestError):
            logger.debug(f"Inside {self.base_dir=}")
            if self._this_executes_only_when_base_dir_exists():
                return True
        return False

    def _this_executes_only_when_base_dir_exists(self) -> bool:
        """Trick the ty-pe checker and provide clear suppress"""
        return True

    @property
    def in_camp(self) -> bool:
        with suppress(NotInForestError):
            logger.debug(f"Inside {self.camp_dir_as_parent=}")
            if self._this_executes_only_when_base_dir_exists():
                return True
        return False

    @property
    def camp_dir_as_parent(self):
        parent: Path | None = recursive_parent(
            path=Path.cwd(), parent_dir_name=self._names.camp_dir
        )
        if parent is None:
            raise NotInCampError
        return parent

    @property
    @PathGuard.dir
    def camp_dir(self) -> Path:
        return self.base_dir / self._names.camp_dir

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
    def tree_file(self, id: int, stem: str) -> Path:
        """Error if not in base"""
        tree_file: str = self._names.tree_file([id, stem])
        return self.tree_dir / tree_file

    @property
    @PathGuard.file(default_content="", raise_error=True)
    def input_prompt(self) -> Path:
        return Path.cwd() / self._names.prompt

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
        roles: list[Path] = []
        if mode in ("all", "global"):
            roles.extend(self.role_dir.glob("*"))
        if mode in ("all", "local"):
            roles.extend(self.camp_role_dir.glob("*"))
        return roles

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
    def conversation_file(
        self, stem: str, suffix: str = ".md", root_dir: Path | None = None
    ) -> Path:
        return self._path_from_stem(stem, suffix, root_dir)

    def _path_from_stem(
        self, stem: str, suffix: str, root_dir: Path | None = None
    ) -> Path:
        suffix: str = suffix if suffix.startswith(".") else f".{suffix}"
        return (root_dir or Path.cwd()) / f"{stem}{suffix}"
