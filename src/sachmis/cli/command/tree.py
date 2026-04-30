from pathlib import Path

from loguru import logger
from sstcore.cli import logger_catch, sargs

from ...config import SachmisConfig, get_config
from ...config.model import ModelFamily
from ...core import capstone as cap
from ...core.model.agent import Model
from ...data import DataManager
from ...utils.parse import model_from_unique
from ...utils.print import printer
from ..args import (
    Async,
    Fire,
    Images,
    PickFile,
    PickImage,
    PickRole,
)
from .fire import confirm_fire

config: SachmisConfig = get_config()


@logger_catch
def tree(
    # Arguments
    file_to_tree: Path,
    # Options for task selection
    pick_role: PickRole = True,
    files: sargs.Files = None,
    pick_file: PickFile = False,
    images: Images = None,
    pick_image: PickImage = False,
    # General Options
    use_async: Async = False,
    # dry_run: DryRun = False,
    direct_fire: Fire = False,
):
    """Load existing tree from path, assemble prompt and fire"""

    with DataManager(forest_required=True) as data:
        data.load_prompt()

        # REFACTOR: collapse with Fire (and others)

        extracted: tuple[str, str] = _extract_from_path(file_to_tree)
        logger.debug(f"{extracted=}")
        model: ModelFamily = _get_model(extracted[0])
        tree_locator: str = _get_locator(extracted[1])

        agents: list[Model] = cap.load_models(
            data, [model], tree_locator=tree_locator
        )

        if not direct_fire and not confirm_fire(data, agents):
            return

        logger.info("Ready to fire")

        dry_run = False
        cap.launch_models(agents, use_async, dry_run)

        printer.title("Models finished to run, storing data, au revoir!")

    logger.info("All processes finished")


def _extract_from_path(file_to_tree: Path) -> tuple[str, str]:
    # MOVE: function of Names
    name_parts: list[str] = file_to_tree.stem.split("_")
    return (name_parts[1], name_parts[2])


def _get_model(raw_string: str) -> ModelFamily:
    if (parsed_model := model_from_unique(raw_string)) is None:
        logger.error(f"Failure for {raw_string=}")
        raise ValueError
    else:
        return parsed_model


def _get_locator(raw_string: str) -> str:
    logger.info(f"{raw_string=}")
    return raw_string
