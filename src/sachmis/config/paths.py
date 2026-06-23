from contextlib import suppress
from pathlib import Path
from typing import Literal

from loguru import logger
from sstcore import PathGuard
from sstcore.config import SstPaths
from sstcore.utils import day_count
from sstcore.utils.path import (
    recursive_parent,
    recursive_root,
)

from ..exceptions import (
    ArborealDataError,
    ArborealTrackingError,
    NotInCampError,
)
from .defaults import Defaults
from .names import Names


class Paths(SstPaths[Names, Defaults]):
    """Assemble paths for project"""

    @property
    def active_biome(self) -> bool:
        return self.unconfirmed_biome_file.exists()

    @property
    def biome_dir(self) -> Path:
        return self.data_home / "biome"

    def biome_file(self, filename: str | None = None) -> Path:
        """Path to active Biome File or Error"""
        try:
            return PathGuard.file(target=self._biome_file(filename))
        except FileNotFoundError as error:
            logger.error(f"Missing biome: {error=}")
        raise ArborealTrackingError("Biome", self._biome_file())

    def _biome_file(self, filename: str | None = None) -> Path:
        """path constructor class"""
        return self.biome_dir / (filename or self._names.biome_file)

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

        biome_filename: str = f"{name.rstrip('.json')}.json"
        new_biome_file: Path = self._biome_file(biome_filename)

        if new_biome_file in self.biome_files:
            raise ArborealDataError("Biome", new_biome_file)

        logger.success(f"Created Path for new Biome: {new_biome_file=}")

        return new_biome_file

    @property
    def iret_camp_dir(self) -> Path:
        root: Path | None = recursive_root(
            # NEXT: control everywhere adapteda!
            path=Path.cwd(),
            indicator=self._names.camp_dir,
        )
        if root is None:
            raise NotInCampError
        return root

    @property
    def inside_camp(self) -> bool:
        """Answer if the current Location is inside any IretCamp"""
        return Path.cwd() == self.iret_camp_dir

    def cwd_location_from_iret(self, strict=True) -> Path:
        """Provide relative Path from camp root to CWD or Raise"""
        return PathGuard.relative(
            target=Path.cwd(), root=self.iret_camp_dir, strict=strict
        )

    def _this_executes_only_when_iret_camp_dir_exists(self) -> bool:
        """Trick the ty-pe checker and provide clear suppress"""
        return True

    @property
    def inside_oasis(self) -> bool:
        with suppress(NotInCampError):
            logger.debug(f"Inside {self.find_oasis=}")
            if self._this_executes_only_when_iret_camp_dir_exists():
                return True
        return False

    @property
    def find_oasis(self):
        parent: Path | None = recursive_parent(
            path=Path.cwd(), parent_dir_name=self._names.camp_dir
        )
        if parent is None:
            raise NotInCampError
        return parent

    @property
    @PathGuard.dir
    def camp_dir(self) -> Path:
        return self.iret_camp_dir / self._names.camp_dir

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
    def tree_file(self, id: int, topic: str) -> Path:
        """Error if not in base"""
        tree_file: str = self._names.tree_stem(id, topic)
        return self.tree_dir / f"{tree_file}.json"

    @property
    @PathGuard.file(default_content="", raise_error=True)
    # FIX: no file outside forest!
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
        stem = f"{day_count()}_{model}_{topic}{suffix}"
        return self.full_response_dir / stem

    @PathGuard.unique(ensure_parent=True)
    def prompt_file(self, write_dir: Path, id: int, topic: str) -> Path:
        prompt_file: str = self._names.prompt_stem(id, topic)
        return write_dir / f"{prompt_file}.md"

    @PathGuard.unique(ensure_parent=True)
    def response_file(
        self, write_dir: Path, id: int, model: str, topic: str
    ) -> Path:
        response_file: str = self._names.response_stem(id, model, topic)
        return write_dir / f"{response_file}.md"
