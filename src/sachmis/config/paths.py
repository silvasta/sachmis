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
        # TODO: local file storage:
        # - check if location base/.camp/files actually make sense
        # - if so, create as well image_dir
        return self.camp_dir / self._names.file_dir

    @property
    @PathGuard.dir
    def role_dir(self) -> Path:
        return self.data_home / "roles"

    @property
    @PathGuard.dir
    def full_response_dir(self) -> Path:
        return self.state_home / "full_respone"

    @PathGuard.unique
    def full_response_path(
        self, topic="", model="", stem=None, suffix="md", prompt_root=None
    ) -> Path:
        stem: str = stem or tree_stem(topic=topic, characteristic=model)
        return self.full_response_dir / f"{stem}.{suffix}"

    def prompt_file(
        self,
        topic: str = "",
        stem: str | None = None,
        suffix: str = ".md",  # LATER: PathGuard.ensure_suffix({.}md) == .md
        prompt_dir: Path | None = None,  # TODO: is this used somewhen?
    ) -> Path:
        """New prompt file name after usage"""
        if prompt_dir is None:
            prompt_dir: Path = Path.cwd()
        if stem is None:  # TASK: name factory! in names!
            stem: str = tree_stem(  # FIX:
                topic=topic,
                characteristic="prompt",
            )
        # TODO: PathGuard!
        return prompt_dir / f"{stem}.{suffix}"

    def answer_file_path(
        self, topic="", model="", stem=None, suffix="md", answer_dir=None
    ) -> Path:
        # TASK: make similar to prompt_file
        answer_dir: Path = answer_dir or Path.cwd()
        stem: str = stem or tree_stem(  # FIX:
            topic=topic,
            characteristic=model,
        )
        # TODO: PathGuard!
        return answer_dir / f"{stem}.{suffix}"
