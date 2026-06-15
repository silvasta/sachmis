import json
from pathlib import Path
from typing import Self

from pydantic import Field
from sstcore.data import FileRegistry, SstFile

from ...exceptions import SachmisDataError


class Role(SstFile):
    path: Path
    content: str
    rating: float = Field(default=5, ge=0, le=10)

    # REFACTOR: check with sstcore.files.sstmodel

    @classmethod
    def load(cls, path: Path) -> Self:
        return cls.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def save(self, json_path: Path | None = None):
        self.json_file(json_path).write_text(self.to_json(), encoding="utf-8")

    def to_json(self) -> str:
        return self.model_dump_json(exclude_defaults=False, indent=2)

    def json_file(self, path: Path | None = None) -> Path:
        if path and path.suffix == ".json":
            return path
        return self.path.with_suffix(".json")

    @classmethod
    def read(cls, path: Path) -> Self:
        return cls(path=path, local_path=path, content=path.read_text())

    def write(self, txt_path: Path | None = None):
        self.txt_file(txt_path).write_text(self.content)

    def txt_file(self, path: Path | None = None) -> Path:
        if path and path.suffix == ".txt":
            return path
        return self.path.with_suffix(".txt")


class RoleRegistry(FileRegistry[Role]):
    """Registry specifically for Roles"""

    def _create_local_file(self, path: Path) -> Role:
        match path.suffix:
            case ".txt":
                return Role.read(path)
            case ".json":
                return Role.load(path)
            case _:
                if path.exists():
                    raise SachmisDataError(f"Invalid suffix for Role: {path=}")
        raise SachmisDataError(f"Path doesn't exist for Role: {path=}")
