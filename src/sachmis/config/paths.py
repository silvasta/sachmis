from pathlib import Path

from silvasta.config.paths import BasePaths
from silvasta.utils import PathGuard
from silvasta.utils.path import (
    find_project_root,
    recursive_parent,
    recursive_root,
)

from .settings import Defaults, Names


class Paths(BasePaths[Names, Defaults]):
    """Assemble paths for project"""

    @property
    @PathGuard.file(raise_error=False)
    def biome_file(self) -> Path:
        return self.data_home / self._names.biome_file

    @property
    # LATER: check here but store value in data?
    def in_base(self) -> bool:
        return (
            recursive_root(
                path=Path.cwd(),
                indicator=self._names.camp_dir,
            )
            is not None
        )

    @property
    # LATER: check here but store value in data?
    def in_camp(self) -> bool:
        return (
            recursive_parent(
                path=Path.cwd(),
                indicator=self._names.camp_dir,
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
    def file_dir(self):
        return self.camp_dir / self._names.file_dir

    @property
    @PathGuard.dir
    def image_dir(self):
        return self.camp_dir / self._names.image_dir

    @property
    @PathGuard.dir
    def role_dir(self) -> Path:
        return self.data_home / "roles"

    @property
    @PathGuard.dir
    def full_response_dir(self) -> Path:
        return self.state_home / "full_respone"

    @PathGuard.unique
    def full_response_path(  # LATER: ensure suffix, .txt==txt
        self, topic="", model="", stem=None, suffix=".txt"
    ) -> Path:
        stem: str = stem or self._names.tree_stem(
            topic=topic, characteristic=model
        )
        return self.full_response_dir / f"{stem}{suffix}"

    @PathGuard.unique
    def prompt_file(  # LATER: PathGuard.ensure_suffix({.}md) == .md
        self, topic: str = "", stem: str | None = None, suffix: str = ".md"
    ) -> Path:
        """New prompt file name after usage"""

        # TASK: name factory! in names!
        # ResponseNames?o
        # - 1 input: topic,models
        # - output for all models, (full)response etc
        # finally paths just provides with proper path

        if stem is None:
            stem: str = stem or self._names.tree_stem(
                topic=topic,
                characteristic="prompt",
            )
        return Path.cwd() / f"{stem}{suffix}"

    def answer_file_path(
        self, topic="", model="", stem=None, suffix=".md"
    ) -> Path:
        stem: str = stem or self._names.tree_stem(
            topic=topic,
            characteristic=model,
        )
        # TODO: PathGuard!
        return Path.cwd() / f"{stem}{suffix}"
