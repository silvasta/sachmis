from pathlib import Path

from pick import pick

from ..core.models import Geminis, Groks, Models


def picked_models() -> list[Models]:
    """Prepare list of 'Models', send to pick, process result"""
    return []


def picked_images() -> list[Path]:
    """Prepare list of 'Models', send to pick, process result"""
    return []


def pick_role(path: Path, pattern: str = "*") -> Path:
    """show all elements at path location and pick one"""

    # NOTE: format role display in pick
    # def format(e: Path) -> str:
    #     words = e.stem.split("-")
    #     return " ".join(w.capitalize() for w in words)

    # add global
    elements: list[Path] = sorted([x for x in path.glob(pattern)])
    title: str = f"Choose System Role: (defined in {path})"
    stem, index = pick([e.stem for e in elements], title)
    # TEXT: works the picker? path back not stem?
    print(f"Role will be set to: {stem}")
    return elements[index]


def pick_from_folder(path: Path, pattern: str = "*") -> str:
    """show all elements at path location and pick one"""

    elements: list = [e.stem for e in path.glob(pattern)]
    title: str = "Choose an element to be set:"
    option, _ = pick(elements, title)
    print(f"You chose {option}")
    return option
