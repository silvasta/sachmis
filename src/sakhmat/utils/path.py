import functools
import re
import shutil
import tomllib
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Union

from loguru import logger


def recursive_root(path: Path, indicator: str) -> Path | None:
    """Find root by indicator iterating parent paths upwards"""
    if (path / indicator).exists():
        return path
    elif path == path.parent:
        return None
    else:
        return recursive_root(path.parent, indicator)


def recursive_parent(path: Path, indicator: str) -> Path | None:
    """Find root by indicator iterating parent paths upwards"""
    if path.parent.name == indicator:
        logger.debug(f"Found {indicator=}")
        return path
    elif path == path.parent:
        logger.debug(f"Not found {indicator=}")
        return None
    else:
        return recursive_parent(path.parent, indicator)


def find_project_root(indicator: Path | str = "pyproject.toml") -> Path:
    """Call recursive function, return Success, Error for fail"""

    search_result: Path | None = recursive_root(Path.cwd(), str(indicator))

    if not search_result:
        print(f"Failed with indicator: {indicator}")
        raise FileNotFoundError("Project root not found!")
    else:
        return search_result


@lru_cache(maxsize=1)
def load_toml(toml_path: Path) -> dict:
    """Reads and caches a toml file"""
    if not toml_path.exists():
        raise FileNotFoundError(f"Invalid {toml_path=}")
    with open(toml_path, "rb") as file:
        return tomllib.load(file)


def dict_to_sns(data: dict):
    """Transform nested dict to SimpleNamespace with dot acces
    e.g., value = key.B.result[0]"""
    if isinstance(data, dict):
        # Recursively convert all values in the dictionary
        return SimpleNamespace(**{k: dict_to_sns(v) for k, v in data.items()})
    elif isinstance(data, list):
        # Recursively convert items in lists (in case they contain dicts)
        return [dict_to_sns(i) for i in data]
    else:
        return data


def pyproject_path() -> Path:
    """Path to own pyproject.toml file"""
    return find_project_root(indicator="pyproject.toml") / "pyproject.toml"


@lru_cache(maxsize=1)
def pyproject_toml() -> dict:
    """Reads and caches the pyproject.toml file"""
    return load_toml(pyproject_path())


def pyproject_sns() -> SimpleNamespace:
    """Load toml file and transform into SimpleNamespace with dot acces"""
    toml: dict = pyproject_toml()
    return dict_to_sns(toml)


def pyproject_name() -> str:
    """Fetches metadata from the [project] section in pyproject.toml"""
    pyproject: SimpleNamespace = pyproject_sns()
    return pyproject.project.name  # INFO: error not catched


def pyproject_log_section() -> SimpleNamespace:
    pyproject: SimpleNamespace = pyproject_sns()
    tool_project_section: SimpleNamespace = getattr(pyproject.tool, pyproject_name())
    return tool_project_section.logging


class PathGuard:
    """Centralized path enforcement toolkit."""

    @staticmethod
    def dir(target: Union[Callable[..., Path], Path]) -> Any:
        """Hybrid: Ensure path is directory and exists, create if missing"""

        # Case 1: Used as a Decorator (@PathGuard.dir)
        if callable(target):

            @functools.wraps(target)
            def wrapper(*args, **kwargs):
                path: Path = target(*args, **kwargs)
                return PathGuard._ensure_dir_logic(path)

            return wrapper
        # Case 2: Used as a Function Call (PathGuard.dir(path))
        return PathGuard._ensure_dir_logic(target)

    @staticmethod
    def _ensure_dir_logic(path: Path) -> Path:
        """The actual implementation logic"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory ensured: {path}")
        return path

    @staticmethod
    def file(raise_error=True, default_content: str | None = None):
        """Ensure path is file, write default content and | or raise error"""

        def decorator(func: Callable[..., Path]):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                path = Path(func(*args, **kwargs))
                if not path.exists():
                    if default_content is not None:  # write first
                        # (user may need fill credentials,e.g. in file)
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(default_content)
                        logger.success(f"Created default file: {path}")
                    if raise_error:
                        raise FileNotFoundError(f"Critical file missing: {path}")
                return path

            return wrapper

        return decorator

    @staticmethod
    def unique(target: Union[Callable[..., Path], Path]) -> Any:
        """Hybrid: Ensures the returned path does NOT exist,
        If it exists, auto-increments suffix (file_1.txt, file_2.txt)"""

        # Case 1: Used as Decorator (@PathGuard.unique)
        if callable(target):

            @functools.wraps(target)
            def wrapper(*args, **kwargs):
                path: Path = target(*args, **kwargs)
                return PathGuard._get_unique_candidate(path)

            return wrapper

        # Case 2: Direct call (PathGuard.unique(path))
        return PathGuard._get_unique_candidate(target)

    @staticmethod
    def _get_unique_candidate(path: Path) -> Path:
        """Internal logic: Appends counter until a free filename is found."""
        path = Path(path)
        if not path.exists():
            return path

        counter = 1
        original_stem = path.stem
        suffix = path.suffix
        parent = path.parent

        # Safety loop to find free slot
        while True:
            new_name = f"{original_stem}_{counter}{suffix}"
            candidate = parent / new_name
            if not candidate.exists():
                return candidate
            counter += 1

    @staticmethod
    def find_sequence(base_target: Path) -> list[Path]:
        """Find all paths of a sequence (base name + auto-incremented versions)
        returns list, sorted by modification time (newest first)"""

        base = Path(base_target)
        parent = base.parent
        if not parent.exists():
            return []

        stem_esc: str = re.escape(base.stem)
        #  re.escape to ensure special chars  don't break regex
        suffix_esc: str = re.escape(base.suffix)
        # regex matches "stem.suffix" OR "stem_digits.suffix"
        pattern: re.Pattern[str] = re.compile(rf"^{stem_esc}(_\d+)?{suffix_esc}$")

        sequence: list[Path] = [
            item for item in parent.iterdir() if pattern.match(item.name)
        ]
        sequence.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        return sequence

    @staticmethod
    def prune(base_target: Path, remaining: int = 5) -> list[Path]:
        """Remove oldest files/dirs from sequence (name_NUM{.*}) until remaining"""

        candidates = PathGuard.find_sequence(base_target)

        if len(candidates) <= remaining:
            return []

        to_delete = candidates[remaining:]
        deleted_paths = []

        for path in to_delete:
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                    logger.info(f"Pruned old dir: {path.name}")
                else:
                    path.unlink()
                    logger.info(f"Pruned old file: {path.name}")
                deleted_paths.append(path)
            except OSError as e:
                logger.error(f"Failed to prune {path}: {e}")

        return deleted_paths

    @staticmethod
    def rotate(source: Path, target: Path, reset: bool = False) -> Path:
        """Moves source (file or dir) to target, handles unique naming collisions,
        if reset=True, recreates empty file or directory at original 'source' location"""
        source = Path(source)
        target = Path(target)

        if not source.exists():
            raise FileNotFoundError(f"Cannot rotate missing path: {source}")

        # Store type for reset logic later
        is_directory = source.is_dir()
        # Ensure destination parent exists
        PathGuard._ensure_dir_logic(target.parent)

        final_target: Path = PathGuard.unique(target)

        shutil.move(str(source), str(final_target))

        try:
            log_src = source.resolve().relative_to(Path.cwd())
            log_dst = final_target.resolve().relative_to(Path.cwd())
        except ValueError:
            log_src = source.name
            log_dst = final_target.name

        logger.debug(f"Rotated: {log_src} -> {log_dst}")

        if reset:
            if is_directory:
                source.mkdir()
                logger.debug(f"Recreated empty directory: {source}")
            else:
                source.touch()
                logger.debug(f"Reset empty file: {source}")

        return final_target
