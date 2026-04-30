from pathlib import Path

from loguru import logger
from pick import pick

from ..config import SachmisConfig, get_config
from ..config.model import Geminis, Groks, ModelFamily
from ..utils.print import printer

config: SachmisConfig = get_config()

# TASK: Check questionary library:
# - improvement to pick for more advanced setups

# TASK: check if picker = Picker() makes sense
# - maybe derived from silvasta.utils.Picker?


def picker(
    elements: list[str], pattern: str = "*", title: str | None = None
) -> str:
    """Show elements from list, select 1 and get name back"""

    option, _ = pick(elements, title)
    print(f"You chose {option}")

    return option


def pick_from_folder(
    path: Path, pattern: str = "*", title: str | None = None
) -> Path:
    """Show elements from folder, select 1 and get path name"""

    # TODO: merge with multiple, 1 func for path-to-folder
    # WARN: throws bad explaining exception for empty folder!
    elements: list = sorted(e.name for e in path.glob(pattern))
    option: str = picker(elements, pattern=pattern, title=title)

    return path / option


def pick_multiple(
    elements: list,
    title: str = "Choose all elements to process:",
    # WARN: forward arguments not completed, look for better solution!
    min_selection_count=1,
    quiet=False,
) -> list[tuple[str, int]]:
    """Show elements, select and get names and index"""

    options_with_index: list[tuple[str, int]] = pick(
        elements,
        title,
        multiselect=True,
        min_selection_count=min_selection_count,
    )

    if not quiet:
        print("You chose:")
        for option, index in options_with_index:
            print(f"{index}: {option}")

    return options_with_index


def pick_multiple_get_name(
    elements: list,
    title: str = "Choose all elements to process:",
    min_selection_count=1,
    quiet=False,
) -> list[str]:
    """Show list elements, pick, return selected names"""

    return [selected[0] for selected in pick_multiple(elements)]


def pick_multiple_get_index(
    elements: list,
    title: str = "Choose all elements to process:",
    min_selection_count=1,
    quiet=False,
) -> list[int]:
    """Show list elements, pick, return selected index"""

    return [selected[1] for selected in pick_multiple(elements)]


def pick_multiple_from_folder(path: Path, pattern: str = "*.*") -> list[Path]:
    """Show elements from folder, select multiple and get path names"""

    if elements := sorted(e.name for e in path.glob(pattern)):
        return [
            path / selected  #
            for selected in pick_multiple_get_name(elements)
        ]
    else:
        print("Nothing to pick")
        return []


def pick_models() -> list[ModelFamily]:

    models_to_pick: list[ModelFamily] = []

    for grok in Groks:
        models_to_pick.append(grok)

    # HACK: General Collector for all (active) models?
    # (check picker,show-app,others)

    for gemini in Geminis:
        models_to_pick.append(gemini)

    selected: list[int] = pick_multiple_get_index(
        elements=models_to_pick,
        title="Choose al l Models to attach",
        min_selection_count=1,
    )
    return [models_to_pick[i] for i in selected]


def pick_files(path: Path | None = None) -> list[Path]:
    """Prepare list of 'Models', send to pick, process result"""

    path: Path = path or config.paths.file_dir
    logger.info(f"Picking files from {path}")

    return pick_multiple_from_folder(path)


# TODO: unify files/images


def pick_images(path: Path | None = None) -> list[Path]:
    """Prepare list of 'Models', send to pick, process result"""

    path: Path = path or config.paths.image_dir
    logger.info(f"Picking images from {path}")

    return pick_multiple_from_folder(path)


def pick_role_from_dir(path: Path, pattern: str = "*") -> Path:
    """show all elements at path location and pick one"""

    # NOTE: format role display in pick
    # def format(e: Path) -> str:
    #     words = e.stem.split("-")
    #     return " ".join(w.capitalize() for w in words)

    # WARN: throws bad explaining exception for empty folder!
    title: str = f"Choose System Role, defined in:\n{path}"
    select: Path = pick_from_folder(path, title=title)

    # TASK: better picker concept

    printer(f"Role will be set to:\n{select}")

    return select


if __name__ == "__main__":
    test = "b"
    match test:
        case "a":
            for model in pick_models():
                print(model.api_name)
        case "b":
            for image in pick_images():
                print(image)
