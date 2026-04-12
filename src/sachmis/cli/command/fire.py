from pathlib import Path

from loguru import logger
from silvasta.cli import logger_catch, sargs

from sachmis.cli import args
from sachmis.config import SachmisConfig, get_config
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

config: SachmisConfig = get_config()


@logger_catch
def fire(
    # Arguments
    models: args.Models = None,
    # Options for task selection
    pick_role: args.PickRole = True,
    files: args.Files = None,
    pick_file: args.PickFile = False,
    images: args.Images = None,
    pick_image: args.PickImage = False,
    # General Options
    use_async: args.Async = False,
    dry_run: sargs.DryRun = False,
    direct_fire: args.Fire = False,
):
    """Prepare models with local prompt and Fire"""

    # INFO: start data context here because of priority of execution:
    # - loading models and prompt before picking files and images
    # - model/prompt failures should not cause unnecessary picks

    with DataManager(forest_required=True) as data:
        data._write_to_cwd = True
        data.load_prompt()

        # MOVE: _prepare... to args?
        models: list[ModelFamily] = _prepare_model_args(models)
        agents: list[Model] = cap.load_models(data, models)

        # MOVE: _prepare... to args?
        files: list[Path] = _prepare_file_args(files, pick_file)
        data.load_files(files)

        # MOVE: _prepare... to args?
        images: list[Path] = _prepare_image_args(images, pick_image)
        data.load_images(images)

        # MOVE: _prepare... to args?
        role: Path | None = _prepare_role(pick_role)
        data.load_role(role)

        if not direct_fire and not confirm_fire(data, agents):
            return

        logger.info("Ready to fire")

        cap.launch_models(agents, use_async, dry_run)

        printer.success("Models finished to run, storing data, au revoir!")

        printer.lines_from_list(
            header="Paths of generated Files",
            title=data.most_recent_topic,
            lines=data.answer_file_path_strings,
        )

    logger.info("All processes finished")


def confirm_fire(data: DataManager, models: list[Model], fire=False) -> bool:

    # TASK: style concept for entire printer story

    while not fire:  # LATER: show this once if input arg fire=True?
        printer.success(
            "Summary of Release",
        )

        printer.title(f"Prompt - {data._prompt.topic}")
        printer.md(data._prompt.text)

        def _lines_from_list_args(name, lines: list):
            # MERGE: if good, either into silvasta.Printer or sachmis.Printer
            return {
                "header": f"{name}: {len(lines)}",
                "title": name,
                "lines": lines,
            }

        printer.lines_from_list(
            **_lines_from_list_args(
                name="Models",
                lines=[model.model.api_name for model in models],
            )
        )

        printer.lines_from_list(
            header=f"Role: {data._role_path.stem if data._role_path else 'No role selected!'}",
            title="Role",
            lines=[data._role or f"{data._role_path=} and {data._role=}"],
        )

        printer.lines_from_list(
            **_lines_from_list_args(
                name="Files",
                lines=[file.name for file in data._files],
            )
        )

        printer.lines_from_list(
            **_lines_from_list_args(
                name="Images",
                lines=[image.name for image in data._images],
            )
        )

        for model in models:  # REFACTOR:
            if model.old_tree_locator:
                printer.title(
                    f"{model.model.unique} is answering to previous response",
                    style="bold black on yellow",
                )
        printer.danger("Last check before deployment")

        match input("type 'ok' to launch, 'r' to reload: "):
            case "ok":
                fire = True
                printer.title("send API request now!", style="green")
            case "r":
                # TODO: case to adapt role,image,model?
                # probably not! either remove r
                data.load_prompt()
            case _:
                printer.yellow(
                    "see you when prompt and command chain is ready!"
                )
                break

    return fire


# MOVE: _prepare... to args?
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


# MOVE: _prepare... to args?
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


# MOVE: _prepare... to args?
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


# MOVE: _prepare... to args?
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
