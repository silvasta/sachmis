from boltons.strutils import slugify
import os
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Literal

from dotenv import load_dotenv
from loguru import logger

from .path import (
    PathGuard,
    find_project_root,
    pyproject_log_section,
    recursive_parent,
)

xdg_data_home = Path(os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share")))
xdg_state_home = Path(os.getenv("XDG_STATE_HOME", os.path.expanduser("~/.local/state")))
xdg_config_home = Path(os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config")))


class ConfigManager:
    """Provides information to connect project- and filesystem data"""

    project_root: Path = find_project_root()
    new_base_tag: str = "NEW BASE"

    def __init__(self, home: Literal["local", "global"] = "local"):
        self.home: Literal["local", "global"] = home
        load_dotenv(self.dotenv_path)
        logger.info("ConfigManager setup completed")

    @property
    @PathGuard.dir
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    @PathGuard.dir
    def input_file_dir(self) -> Path:
        return self.data_dir / "input-files"

    @property
    @PathGuard.dir
    def config_home(self) -> Path:
        if self.home == "local":
            home: Path = self.data_dir / "config"
        elif self.home == "global":
            home: Path = xdg_config_home
        return home

    @property
    @PathGuard.file(
        default_content="# Fill at least 1, delete others\nXAI_API_KEY=\nGEMINI_API_KEY="
    )
    def dotenv_path(self) -> Path:
        return xdg_config_home / "sachmis/.env"

    @property
    @PathGuard.dir
    def data_home(self) -> Path:
        if self.home == "local":
            home: Path = self.data_dir / "share"
        elif self.home == "global":
            home: Path = xdg_data_home
        return home

    @property
    @PathGuard.dir
    def state_home(self) -> Path:
        if self.home == "local":
            home: Path = self.data_dir / "state"
        elif self.home == "global":
            home: Path = xdg_state_home
        return home

    @property
    def base_name(self) -> str:
        return "base"

    @property
    def camp_name(self) -> str:
        return ".camp"

    @property
    @PathGuard.dir
    def camp_dir(self):
        return self.forest_dir / self.camp_name if self.forest_dir else None

    @property
    @PathGuard.dir
    def file_dir(self):
        return self.camp_dir / "files" if self.forest_dir else None

    @property
    def in_camp(self) -> bool:
        return recursive_parent(Path.cwd(), self.camp_name) is not None

    @property
    def forest_dir(self) -> Path | None:
        """in_base"""
        # NOTE: base_dir? unify names somewhen
        try:
            return find_project_root(self.forest_file_name)
        except FileNotFoundError:
            return None

    @property
    def forest_file_name(self) -> str:
        return ".forest.json"

    @property
    def forest_file(self) -> Path | None:
        return self.forest_dir / self.forest_file_name if self.forest_dir else None

    @property
    def day_count(self):
        return str((date.today() - date(2000, 1, 1)).days)

    @property
    def default_prompt_name(self) -> str:
        return "prompt.md"

    def tree_stem(self, topic: str = "", characteristic: str = "") -> str:
        """Assemble file (or folder) name"""
        topic: str = slugify(topic, delim="-")
        return "_".join(
            [
                name_part
                for name_part in [self.day_count, topic, characteristic]
                if name_part != ""
            ]
        )

    def prompt_file_path(
        self, topic="", stem=None, suffix="md", prompt_dir=None
    ) -> Path:
        """After processing"""
        prompt_dir: Path = prompt_dir or Path.cwd()
        stem: str = stem or self.tree_stem(
            topic=topic,
            characteristic="prompt",
        )
        return prompt_dir / f"{stem}.{suffix}"

    def answer_file_path(
        self, topic="", model="", stem=None, suffix="md", answer_dir=None
    ) -> Path:
        answer_dir: Path = answer_dir or Path.cwd()
        stem: str = stem or self.tree_stem(
            topic=topic,
            characteristic=model,
        )
        return answer_dir / f"{stem}.{suffix}"

    @property
    @PathGuard.dir
    def full_response_dir(self) -> Path:
        return self.state_home / "full_respone"

    @PathGuard.unique  # TEST: unique here sensefull?
    def full_response_path(
        self, topic="", model="", stem=None, suffix="md", prompt_root=None
    ) -> Path:
        stem: str = stem or self.tree_stem(topic=topic, characteristic=model)
        return self.full_response_dir / f"{stem}.{suffix}"

    @property
    @PathGuard.dir
    def role_dir(self) -> Path:
        return self.data_home / "roles"

    @property
    @PathGuard.dir
    def log_dir(self):
        return self.project_root / "logs"

    @property
    @PathGuard.file(raise_error=False, default_content="")
    def log_file_path(self):
        log_config: SimpleNamespace = pyproject_log_section()
        return self.log_dir / log_config.file_name

    @staticmethod
    def from_env(key: str):
        # TODO: check using this in Model
        return os.getenv(key=key)

    def load_config(self):
        pass
