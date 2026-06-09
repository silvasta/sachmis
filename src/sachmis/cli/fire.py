from pathlib import Path

from loguru import logger
from sstcore.cli import sargs
from sstcore.data import SstFile

from ..config import SachmisConfig, get_config
from ..config.models import ModelFamily
from ..core import capstone
from ..core.model import Model
from ..data import DataManager
from ..data.files import CampManager, UploadFile
from ..exceptions.data import DataRuntimeError
from ..tui.selector import file_selector, model_selector, role_selector
from ..utils.parse import parse_raw_models
from ..utils.print import printer
from . import args

config: SachmisConfig = get_config()

DEBUG = True


def fire(
    # Arguments
    models: args.Models = None,
    # sprout: args.Sprout = False,
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
    """Prepare Models with Local Prompt and Fire"""

    with capstone.Fire() as session:
        # PLUG:
        # PLUG:
        # PLUG:
        # NEXT: check cli.command._rollout
        # TASK: data.handler provide model subset needed!
        models: list[ModelFamily] = _prepare_model_args(session.data, models)
        agents: list[Model] = session.load_models(models)

        # NEXT: function of camp
        files: list[UploadFile] = _prepare_file_args(
            session.data.camp, files, pick_file
        )
        session.data.load_files(files)

        # NEXT: function of camp
        images: list[SstFile] = _prepare_image_args(
            session.data.camp, images, pick_image
        )
        session.data.load_images(images)

        # NEXT: function of camp
        role: Path | None = _prepare_role(pick_role)
        session.data.load_role(role)

        if not direct_fire and not confirm_fire(agents, session.data):
            return

        logger.info("Ready to Fire")

        session.launch(use_async, dry_run)

        printer.success("Models finished to run, storing data, au revoir!")

        printer.lines(
            header="Paths of generated Files",
            # IMPORTANT: no box around! plus nvim command
            title=session.data.prompt.topic,
            lines=session.data.result_files(),
        )

    logger.info("All processes finished")


def confirm_fire(models: list[Model], data: DataManager) -> bool:

    printer.special("Summary of Release")

    # NEXT: prompt to... Sprout?
    printer.title(f"Prompt - {data.prompt.topic}")
    printer.md(data.prompt.content)

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
    # NEXT: but with previons response
    # printer.model_table()

    printer.danger("Last check before deployment")

    match input("type 'ok' to launch: "):  # NEXT: check rich.prompt.Ask
        case "ok":
            printer.title("send API request now!", style="green")
            return True
        case _:
            printer(
                "see you when prompt and command chain is ready!",
                style="yellow",
            )
            return False


def _prepare_model_args(
    data: DataManager,  # NEXT: sprout
    models: list[str] | None,  # REMOVE: data.handler!
) -> list[ModelFamily]:
    printer.title("Selecting Models...")

    # NEXT: fix with new setup
    if models and (parsed_models := parse_raw_models(models)):
        printer.header(f"...{len(parsed_models)} selected for pipeline")
        return parsed_models

    match len(scanned_models := data.handler.scanned_models):  # TEST:
        case 0:
            return model_selector(multi_select=True)
        case 1:
            selected_model: ModelFamily = scanned_models[0]
        case _:
            selected_model: ModelFamily = model_selector(
                models=scanned_models,
                multi_select=False,
            )[0]  # TASK: multi output, bipart tree

    return [selected_model]


# NEXT: move to camp?
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
            raise DataRuntimeError(f"Failed to Import {file=}")

    printer.md(f"...{len(prepared_files)} files selected for pipeline")

    return prepared_files


# NEXT: move to camp?
# MOVE: _prepare... to args?
def _prepare_image_args(
    camp: CampManager, images: list[Path] | None, pick_image: bool
) -> list[SstFile]:

    printer.title("Preparing Images...")

    prepared_images: list[SstFile] = []

    # NEXT: same as files?
    # REFACTOR:
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
            raise DataRuntimeError(f"Failed to Import {file=}")

    printer.md(f"...{len(prepared_images)} images selected for pipeline")

    return prepared_images


def _prepare_role(pick_role: bool) -> Path | None:
    printer.title("Preparing Role...")

    if pick_role:
        roles: list[Path] = config.paths.role_paths(mode="all")  # PARAM:
        role: Path = role_selector(roles)
        logger.info(f"Selected Role: {role.stem}")
    else:
        logger.info("no role selected and no picker")
        role = None

    return role
