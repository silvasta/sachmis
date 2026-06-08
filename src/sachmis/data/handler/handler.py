from abc import abstractmethod
from pathlib import Path

from sstcore import PathGuard

from ...config import SachmisConfig, get_config
from ...config.models import ModelFamily

config: SachmisConfig = get_config()


class DataHandler:
    """Provide input/output data from Sprout to Forest or Rollout"""

    _result_files: list[Path] = []

    @abstractmethod
    def models() -> list[ModelFamily]:
        # NEXT: maybe an arg for pick or so
        """Provide subset of Models according to observed Data state"""

    @abstractmethod
    def prompt_text():
        """Provide the prepared content for the Prompt"""
        # INFO: for fire:
        # - not possible to directly create prompt, id might be unknown

    @abstractmethod
    def process(self, **kwargs):
        """Process the received Prompt or Response with your Schema"""

    def result_files(self, root_dir: Path | None = None) -> list[Path]:
        """Provide relative Paths of already written result files"""
        # NEXT: simplify, use cwd, No root_dir arg!
        # - relative? to cwd, base or not at all?
        return list(
            PathGuard.relative(target=path, root=root_dir, strict=False)
            for path in self._result_files
        )

    @property
    def result_file_paths(self) -> list[Path]:
        """Provide absolute Paths of already written result files"""
        return self._result_files


class FileRollout(DataHandler):
    """Manage Prompt and Response write to Forest dir"""
