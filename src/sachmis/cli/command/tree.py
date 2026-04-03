from pathlib import Path

from loguru import logger
from silvasta.cli.setup import logger_catch

from sachmis.cli.args import (
    Async,
    DryRun,
    Files,
    Fire,
    Images,
    PickFile,
    PickImage,
    PickRole,
)
from sachmis.config.manager import config
from sachmis.config.model import ModelFamily
from sachmis.core import capstone as cap
from sachmis.core.model.agent import Model
from sachmis.data import DataManager
from sachmis.utils.parse import (
    reversed_name_from_unique,
)
from sachmis.utils.picker import (
    pick_files,
    pick_images,
    pick_models,
    pick_role_from_dir,
)
from sachmis.utils.print import printer

from .fire import confirm_fire


@logger_catch
def tree(
    # Arguments
    file_to_tree: Path,
    # Options for task selection
    pick_role: PickRole = True,
    files: Files = None,
    pick_file: PickFile = False,
    images: Images = None,
    pick_image: PickImage = False,
    # General Options
    use_async: Async = False,
    dry_run: DryRun = False,
    direct_fire: Fire = False,
):
    """Load models and data, assemble prompt and fire"""

    with DataManager(forest_required=True) as data:
        data._write_to_cwd = True
        data.load_prompt()

        extracted: tuple[str, str] = _extract_from_path(file_to_tree)
        logger.debug(f"{extracted=}")
        model: ModelFamily = _get_model(extracted[0])
        tree_locator: str = _get_locator(extracted[1])

        agents: list[Model] = cap.load_models(
            data, [model], tree_locator=tree_locator
        )

        files: list[Path] = _prepare_file_args(files, pick_file)
        data.load_files(files)

        images: list[Path] = _prepare_image_args(images, pick_image)
        data.load_images(images)

        role: Path | None = _prepare_role(pick_role)
        logger.debug("at role")
        data.load_role(role)

        if not direct_fire and not confirm_fire(data, agents):
            return

        logger.info("Ready to fire")

        cap.launch_models(agents, use_async, dry_run)

        printer.title("Models finished to run, storing data, au revoir!")

        printer.preview(
            title="Paths of generated Files",
            lines=[str(answer) for answer in data._answer_file_paths],
        )

    logger.info("All processes finished")


def _extract_from_path(file_to_tree: Path) -> tuple[str, str]:
    # TODO: function of Names
    name_parts: list[str] = file_to_tree.stem.split("_")
    return (name_parts[1], name_parts[2])


def _get_model(raw_string: str) -> ModelFamily:
    if (parsed_model := reversed_name_from_unique(raw_string)) is None:
        logger.error(f"Failure for {raw_string=}")
        raise ValueError
    else:
        return parsed_model


def _get_locator(raw_string: str) -> str:
    logger.info(f"{raw_string=}")
    return raw_string


def _prepare_model_args(models: list[str] | None) -> list[ModelFamily]:

    printer.title("Preparing Models...")

    models: list[ModelFamily] = (
        [
            parsed_model
            for model_unique in models
            if (parsed_model := reversed_name_from_unique(model_unique))
            is not None
        ]
        if models is not None
        else pick_models()
    )
    logger.debug(f"loading {len(models)=}")

    if not models:
        raise AttributeError("No valid models parsed from input...")

    printer.md(f"...{len(models)=} selected for pipeline")

    return models


def _prepare_file_args(
    files: list[Path] | None, pick_file: bool
) -> list[Path]:

    printer.title("Preparing Files...")

    files: list[Path] = [
        *(files or []),
        *(pick_files() if pick_file else []),
    ]
    logger.debug(f"appending {len(files)=}")

    for file in files:
        if not file.exists():
            raise AttributeError(f"Invalid {file=}")

    printer.md(f"...{len(files)} files selected for pipeline")

    return files


def _prepare_image_args(
    images: list[Path] | None, pick_image: bool
) -> list[Path]:

    printer.title("Preparing Images...")

    images: list[Path] = [
        *(images or []),
        *(pick_images() if pick_image else []),
    ]
    logger.debug(f"loading {len(images)=}")

    for image in images:
        if not image.exists():
            raise AttributeError(f"Invalid {image=}")

    printer.md(f"...{len(images)} images selected for pipeline")

    return images


def _prepare_role(pick_role: bool) -> Path | None:

    printer.title("Preparing Role...")

    role: Path | None = (
        pick_role_from_dir(config.paths.role_dir) if pick_role else None
    )
    if role:
        logger.info(f"Selected Role: {role.stem}")
    else:
        logger.info("no role selected")

    return role
