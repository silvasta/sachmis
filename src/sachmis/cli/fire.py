from pathlib import Path

from loguru import logger
from sstcore.cli import sargs
from sstcore.data import SstFile

from ..config import config
from ..core import capstone
from ..core.model import Model
from ..data import DataManager
from ..data.camp import CampManager, UploadFile
from ..data.conversation import SelectedSproutData
from ..exceptions.data import DataRuntimeError
from ..tui import selector
from ..utils.parse import parse_raw_models
from ..utils.print import printer
from . import args
from .canvas.model import model_family_table

DEBUG = True


def fire(
    # Arguments
    models: args.Models = None,
    # sprout: args.Sprout = False, # TODO: some partial select
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
        models: list[SelectedSproutData] = _prepare_model_args(session, models)
        agents: list[Model] = session.load_models(models)

        # TODO: show models here first...?

        files: list[UploadFile] = _prepare_file_args(
            session.data.camp, files, pick_file
        )
        session.data.load_files(files)

        images: list[SstFile] = _prepare_image_args(
            session.data.camp, images, pick_image
        )
        session.data.handler.prompt.attach_images(images)

        role: Path | None = _prepare_role(pick_role)
        session.data.load_role(role)

        if not direct_fire and not confirm_fire(agents, session.data):
            return

        logger.info("Ready to Fire")

        session.launch(use_async, dry_run)

        printer.success("Models finished to run, storing data, au revoir!")
        printer.title("Paths of generated Files")
        printer(paths := session.data.front.result_files_relative())

        # TODO: improve nvim handling
        printer(f"nvim {' '.join(str(p) for p in paths)}")

    logger.info("All processes finished")


def confirm_fire(models: list[Model], data: DataManager) -> bool:

    printer.special("Summary of Release")

    # LATER:
    # TASK: Prompt Print - including files, images, role

    printer.title(f"Prompt - {(prompt := data.handler.prompt)}")
    printer.md(prompt.content)

    printer.lines_with_len(
        name="Models",
        lines=[model.model.api_name for model in models],
    )

    printer.lines(
        header=f"Role: {prompt.role.path.stem if prompt.role else 'No role selected!'}",
        title="Role",
        lines=[
            prompt.role.content if prompt.role else "build more roles in camp"
        ],
    )

    printer.lines_with_len(
        name="Files",
        lines=[file.name for file in prompt.files],
    )

    printer.lines_with_len(
        name="Images",
        lines=[image.name for image in prompt.images],
    )

    model_family_table(selection=[model.sprout.model for model in models])

    printer.danger("Last check before deployment")

    match input("type 'ok' to launch: "):  # LATER: check rich.prompt.Ask
        case "ok":
            printer.title("send API request now!", style="green")
            return True
        case _:
            printer(
                "see you when prompt and command chain is ready!",
                style="yellow",
            )
            return False  # TASK: id loss?


def _prepare_model_args(
    session: capstone.Fire, models: list[str] | None, multi_select=True
) -> list[SelectedSproutData]:

    printer.debug(
        "Start of Selector",
        session.data.front.models(),
        stop=True,
        # NEXT: select
        # NEXT: select
        # NEXT: select
        # NEXT: select
    )
    printer.title("Model Selection")

    if models and (parsed_models := parse_raw_models(models)):
        text = f"{len(parsed_models)} Models parsed for Pipeline"
        printer.header(text)
        return SelectedSproutData.from_zero(parsed_models)

    match len(scanned_models := session.data.front.models()):  # TEST:
        case 0:
            return SelectedSproutData.from_zero(
                selector.model_family(multi_select=True)
            )
        case 1:
            return [SelectedSproutData.from_scan(scanned_models.pop())]
        case _:
            return selector.model_from_scan(
                models=scanned_models,
                multi_select=multi_select,
            )


def _prepare_file_args(
    camp: CampManager, files: list[Path] | None, pick_file: bool
) -> list[UploadFile]:  # LATER:: as function of camp

    # REFACTOR: files and images, simple function from Camp
    printer.title("Preparing Files...")

    prepared_files: list[UploadFile] = []

    if pick_file:  # Pick first to avoid picking as well new added files
        selected_files: list[Path] = selector.file_registry(files=camp.files)
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

    prepared_files.extend(camp.prepare_and_load(files))
    printer.title(f"...{len(prepared_files)} files selected for pipeline")

    return prepared_files


def _prepare_image_args(
    camp: CampManager, images: list[Path] | None, pick_image: bool
) -> list[SstFile]:  # LATER:: as function of camp

    # REFACTOR: files and images, simple function of Camp
    printer.title("Preparing Images...")

    prepared_images: list[SstFile] = []

    if pick_image:  # TODO: use ListSelector? or unify with _prepare_file_args
        selected_images: list[Path] = selector.file_registry(files=camp.images)
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

    if (local_files := config().paths.local_file_dir).exists():
        camp.images.absorb_from_path(local_files)

    for image in prepared_images:
        if not image.confirm_local_status(camp.images.local_root):
            raise DataRuntimeError(f"Failed to Import {file=}")

    printer.md(f"...{len(prepared_images)} images selected for pipeline")

    return prepared_images


def _prepare_role(pick_role: bool) -> Path | None:
    # TASK: extend to gathering statistics, creating layouts
    # LATER:: as function of camp

    printer.title("Preparing Role...")

    if pick_role:
        roles: list[Path] = config().paths.role_paths(mode="all")  # PARAM:
        role: Path = selector.role_path(roles)
        logger.info(f"Selected Role: {role.stem}")
    else:
        logger.info("no role selected and no picker")
        role = None

    return role
