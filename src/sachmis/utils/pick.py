from pathlib import Path


# TASK: use silvasta.utils.pick
# - simplify functions here
# - outsource shared logic

from silvasta.utils.pick import (
    pick_from_folder,
    pick_multiple_from_folder,
)


def picked_models() -> list[Models]:
    """Prepare list of 'Models', send to pick, process result"""
    return []


def picked_images(path: Path) -> list[Path]:
    """Prepare list of 'Models', send to pick, process result"""
    return pick_multiple_from_folder(path)


def pick_role(path: Path, pattern: str = "*") -> Path:
    """show all elements at path location and pick one"""

    # NOTE: format role display in pick
    # def format(e: Path) -> str:
    #     words = e.stem.split("-")
    #     return " ".join(w.capitalize() for w in words)

    title: str = f"Choose System Role: (defined in {path})"
    select: Path = pick_from_folder(path, title=title)

    print(f"Role will be set to: {select}")

    return select
