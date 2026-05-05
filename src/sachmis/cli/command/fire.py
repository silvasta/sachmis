from pathlib import Path

from loguru import logger
from sstcore.cli import logger_catch, sargs
from sstcore.data import SstFile

from ...config import SachmisConfig, get_config
from ...config.model import ModelFamily
from ...core import capstone as cap
from ...core.model import Model
from ...data import DataManager
from ...data.files import CampManager, UploadFile
from ...exceptions.data import DataManagerRuntimeError
from ...tui.selector import (
    file_selector,
    linear_selector,
    model_selector,
    role_selector,
)
from ...utils.parse import parse_raw_models
from ...utils.print import printer
from .. import args

config: SachmisConfig = get_config()

DEBUG = True


@logger_catch
def fire(
    # Arguments
    models: args.Models = None,
    sprout: args.Sprout = False,
    # Options for task selection
    pick_role: args.PickRole = True,
    files: sargs.Files = None,
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

    with DataManager(biome=True, forest=True) as data:
        data.load_prompt()
        data.scan_dir_for_models()

        models: list[ModelFamily] = _prepare_model_args(data, models, sprout)
        agents: list[Model] = cap.load_models(data, models)

        files: list[UploadFile] = _prepare_file_args(
            data.camp, files, pick_file
        )
        data.load_files(files)

        images: list[SstFile] = _prepare_image_args(
            data.camp, images, pick_image
        )
        data.load_images(images)

        role: Path | None = _prepare_role(pick_role)
        data.load_role(role)

        if not direct_fire and not confirm_fire(data, agents):
            return

        logger.info("Ready to fire")

        cap.launch_models(agents, use_async, dry_run)

        printer.success("Models finished to run, storing data, au revoir!")

        printer.lines(
            header="Paths of generated Files",
            title=data.prompt.topic,
            lines=data._answer_file_paths,
        )

    logger.info("All processes finished")


def confirm_fire(data: DataManager, models: list[Model]) -> bool:

    printer.success(
        "Summary of Release",
    )

    printer.title(f"Prompt - {data.prompt.topic}")
    printer.md(data.prompt.text)

    printer.lines_with_len(
        name="Models",
        lines=[model.model.api_name for model in models],
    )

    printer.lines(
        header=f"Role: {data._role_path.stem if data._role_path else 'No role selected!'}",
        title="Role",
        lines=[data._role or f"{data._role_path=} and {data._role=}"],
    )

    printer.lines_with_len(
        name="Files",
        lines=[file.name for file in data.prompt.files],
    )

    printer.lines_with_len(
        name="Images",
        lines=[image.name for image in data.prompt.images],
    )

    for model in models:
        if model.sprout.previous_response_id:
            printer.title(
                f"{model.model.unique} is answering to previous response",
                style="bold black on yellow",
            )
    printer.danger("Last check before deployment")

    match input("type 'ok' to launch: "):
        case "ok":
            printer.title("send API request now!", style="green")
            fire = True
        case _:
            printer(
                "see you when prompt and command chain is ready!",
                style="yellow",
            )
            fire = False

    return fire


# MOVE: _prepare... to args?
def _prepare_model_args(
    data: DataManager,
    models: list[str] | None,
    sprout: bool = False,
    with_dummy=DEBUG,
) -> list[ModelFamily]:

    printer.title("Preparing Models...")

    if models and (parsed_models := parse_raw_models(models)):
        logger.debug(f"loading {len(parsed_models)=}")
        printer.md(f"...{len(parsed_models)} selected for pipeline")
        return parsed_models

    match len(existing_models := data.parse_scanned_models()):
        case 0:
            return model_selector(multi_select=True, with_dummy=with_dummy)
        case 1:
            selected_model: ModelFamily = existing_models[0]
            model_name: str = selected_model.unique
            if sprout:  # LATER: dataclass for sprout_folder_locator
                sprouts: dict[str, str] = data.neighbours_formated(model_name)
                if locator := linear_selector(sprouts):
                    data.set_file_system_locator(locator[0], model_name)
        case _:
            selected_model: ModelFamily = model_selector(
                # FAIL for multiple same models...
                existing_models,
                multi_select=False,
                with_dummy=with_dummy,
            )[0]
            data._write_dir_name = data.prompt.topic

    return [selected_model]


# MOVE: _prepare... to args?
def _prepare_file_args(
    camp: CampManager, files: list[Path] | None, pick_file: bool
) -> list[UploadFile]:

    printer.title("Preparing Files...")

    prepared_files: list[UploadFile] = []

    if pick_file:  # Pick first to avoid picking as well new added files
        selected_files: list[Path] = file_selector(files=camp.files)
        for path in selected_files:
            match len(file := camp.files.get_files_by_path(path)):
                case 0:
                    logger.error(f"File not found in UploadRegistry: {path}")
                case 1:
                    file: UploadFile = file[0]
                    prepared_files.append(file)
                    logger.debug(f"added new file: {file.description}")
                case _:
                    logger.error(f"Multiple files with: {path}, {file=}")

    if files:  # Mirror = copy for CLI provided links
        prepared_files.extend(camp.files.mirror_from_path(source=files))

    if (local_files := get_config().paths.local_file_dir).exists():
        camp.files.absorb_from_path(local_files)
        # LATER: remove  the folder (or just content) afterwards?

    for file in prepared_files:
        if not file.confirm_local_status(camp.files.local_root):
            # TODO: better Error
            raise DataManagerRuntimeError(f"Failed to Import {file=}")

    printer.md(f"...{len(prepared_files)} files selected for pipeline")

    return prepared_files


# MOVE: _prepare... to args?
def _prepare_image_args(
    camp: CampManager, images: list[Path] | None, pick_image: bool
) -> list[SstFile]:

    printer.title("Preparing Images...")

    prepared_images: list[SstFile] = []

    if pick_image:  # Pick first to avoid picking as well new added files
        # TODO: use ListSelector? or unify with _prepare_file_args
        selected_images: list[Path] = file_selector(files=camp.images)
        for path in selected_images:
            match len(file := camp.images.get_files_by_path(path)):
                case 0:
                    logger.error(f"File not found in UploadRegistry: {path}")
                case 1:
                    file: SstFile = file[0]
                    prepared_images.append(file)
                    logger.debug(f"added new file: {file.description}")
                case _:
                    logger.error(f"Multiple files with: {path}, {file=}")

    if images:  # Mirror = copy for CLI provided links
        prepared_images.extend(camp.images.mirror_from_path(source=images))

    if (local_files := get_config().paths.local_file_dir).exists():
        camp.images.absorb_from_path(local_files)

    for image in prepared_images:
        if not image.confirm_local_status(camp.images.local_root):
            raise DataManagerRuntimeError(f"Failed to Import {file=}")

    printer.md(f"...{len(prepared_images)} images selected for pipeline")

    return prepared_images


# MOVE: _prepare... to args?
def _prepare_role(pick_role: bool) -> Path | None:

    printer.title("Preparing Role...")

    if pick_role:
        roles: list[Path] = config.paths.role_paths(mode="all")
        role: Path | None = role_selector(roles)
    else:
        role = None

    if role:
        logger.info(f"Selected Role: {role.stem}")
    else:
        logger.info("no role selected")

    return role
