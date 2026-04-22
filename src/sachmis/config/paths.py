from pathlib import Path

from silvasta.config import SstPaths
from silvasta.utils import PathGuard
from silvasta.utils.path import (
    find_project_root,
    recursive_parent,
    recursive_root,
)

from .defaults import Defaults
from .names import Names


class Paths(SstPaths[Names, Defaults]):
    """Assemble paths for project"""

    @property
    def biome_file(self) -> Path:
        return self.data_home / self._names.biome_file

    # NEXT: biome_file calls this
    # - pathguard.unique? better in data
    # def biome_from_name

    @property
    # LATER: check here but store value in data?
    def in_base(self) -> bool:
        return (
            recursive_root(path=Path.cwd(), indicator=self._names.camp_dir)
            is not None
        )

    @property
    # LATER: check here but store value in data?
    def in_camp(self) -> bool:
        return (
            recursive_parent(
                path=Path.cwd(), parent_dir_name=self._names.camp_dir
            )
            is not None
        )

    @property
    def base_dir(self) -> Path:
        """Error if not in base"""
        return find_project_root(indicator=self._names.camp_dir)

    @property
    @PathGuard.dir
    def camp_dir(self):
        """Error if not in base"""
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
        # MOVE: Names
        return self.camp_dir / f"t_{id}_{stem}.json"

    @property
    @PathGuard.dir
    # TODO: check local_file_dir
    def file_dir(self):
        return self.camp_dir / self._names.file_dir

    @property
    @PathGuard.dir
    def image_dir(self):
        return self.camp_dir / self._names.image_dir

    @property
    @PathGuard.dir
    def role_dir(self) -> Path:
        return self.data_home / "roles"  # PARAM:

    def get_role_paths(self) -> list[Path]:
        return list(self.role_dir.glob("*"))

    # LATER: move function for (inactive) roles, + create  function

    @property
    @PathGuard.dir
    def inactive_role_dir(self) -> Path:
        return self.role_dir.with_stem(f"inactive-{self.role_dir.stem}")

    def get_inactive_role_paths(self) -> list[Path]:
        return list(self.inactive_role_dir.glob("*"))

    @property
    @PathGuard.dir
    def full_response_dir(self) -> Path:
        return self.state_home / "full_respone"

    @PathGuard.unique
    def full_response(self, topic="", model="", suffix=".txt") -> Path:
        stem: str = self._names.sprout_stem(topic=topic, spec=model)
        return self.full_response_dir / f"{stem}{suffix}"

    @PathGuard.unique
    def prompt_file(self, topic: str, suffix: str = ".md") -> Path:
        """New prompt file name after usage"""
        prompt_stem: str = self._names.sprout_stem(topic=topic, spec="prompt")
        return Path.cwd() / f"{prompt_stem}{suffix}"

    @PathGuard.unique
    def answer_file(
        # TASK: create relative path
        self,
        topic: str,
        locator: str,
        model: str,
        suffix=".md",
    ) -> Path:
        answer_stem: str = self._names.sprout_stem(
            topic=topic, locator=locator, spec=model
        )
        return Path.cwd() / f"{answer_stem}{suffix}"
