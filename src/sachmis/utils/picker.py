from pathlib import Path

from loguru import logger
from silvasta.utils.pick import (
    pick_from_folder,
    pick_multiple_from_folder,
    pick_multiple_get_index,
)

from sachmis.config import SachmisConfig, get_config
from sachmis.config.model import Geminis, Groks, ModelFamily
from sachmis.utils.print import printer

config: SachmisConfig = get_config()

# TASK: Check questionary library:
# - improvement to pick for more advanced setups

# TASK: check if picker = Picker() makes sense
# - maybe derived from silvasta.utils.Picker?


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
