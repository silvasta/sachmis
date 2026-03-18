from pathlib import Path

from boltons.strutils import slugify
from pydantic import Field
from silvasta.config.settings import (
    BaseDefaults,
    BaseNames,
    BasePaths,
    Settings,
)
from silvasta.utils import PathGuard, day_count
from silvasta.utils.path import find_project_root, recursive_parent


class Names(BaseNames):
    new_base_tag: str = "NEW BASE"  # used for log write ans search

    base: str = "base"
    camp: str = ".camp"
    forest_file: str = ".forest.json"
    prompt: str = "prompt.md"


class Defaults(BaseDefaults):
    dot_env_content: str = """
    # Fill at least 1, delete others
    XAI_API_KEY=
    GEMINI_API_KEY=
    """


class ProjectSettings(Settings):
    names: Names = Field(default_factory=Names)
    defaults: Defaults = Field(default_factory=Defaults)


def tree_stem(topic: str = "", characteristic: str = "") -> str:
    """Assemble file (or folder) name"""
    # MOVE: either to Names or create: class Config(ConfigManager)
    topic: str = slugify(topic, delim="-")
    return "_".join(
        [
            name_part
            for name_part in [str(day_count()), topic, characteristic]
            if name_part != ""
        ]
    )


class Paths(BasePaths):
    """Assemble paths for project"""

    _names: Names
    _defaults: Defaults

    @property
    def forest_dir(self) -> Path | None:
        """in_base"""  # TODO: handle non better
        try:
            return find_project_root(self._names.forest_file)
        except FileNotFoundError:
            return None

    @property
    def forest_file(self) -> Path | None:
        return (
            self.forest_dir / self._names.forest_file
            if self.forest_dir
            else None
        )

    @property
    def in_camp(self) -> bool:
        # TASK: something like this as check before None handling
        return recursive_parent(Path.cwd(), self._names.camp) is not None

    @property
    @PathGuard.dir
    def camp_dir(self):  # TODO: handle non better
        return self.forest_dir / self._names.camp if self.forest_dir else None

    @property
    @PathGuard.dir
    def file_dir(self):
        return self.camp_dir / "files" if self.forest_dir else None

    def prompt_file_path(
        self, topic="", stem=None, suffix="md", prompt_dir=None
    ) -> Path:
        """After processing"""
        prompt_dir: Path = prompt_dir or Path.cwd()
        stem: str = stem or tree_stem(  # FIX:
            topic=topic,
            characteristic="prompt",
        )
        return prompt_dir / f"{stem}.{suffix}"

    def answer_file_path(
        self, topic="", model="", stem=None, suffix="md", answer_dir=None
    ) -> Path:
        answer_dir: Path = answer_dir or Path.cwd()
        stem: str = stem or tree_stem(  # FIX:
            topic=topic,
            characteristic=model,
        )
        return answer_dir / f"{stem}.{suffix}"

    @property
    @PathGuard.dir
    def full_response_dir(self) -> Path:
        return (
            self.state_home / "full_respone"
        )  # TODO: see what is still needed

    @PathGuard.unique
    def full_response_path(
        self, topic="", model="", stem=None, suffix="md", prompt_root=None
    ) -> Path:
        stem: str = stem or tree_stem(topic=topic, characteristic=model)
        return self.full_response_dir / f"{stem}.{suffix}"

    @property
    @PathGuard.dir
    def role_dir(self) -> Path:
        return self.data_home / "roles"  # TODO: see what is still needed
