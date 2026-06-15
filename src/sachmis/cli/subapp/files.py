from loguru import logger
from sstcore.cli import SafeTyper, sargs

from ...config import SachmisConfig, get_config
from ...data.arboreal import Forest
from ...data.camp import CampManager
from ...data.files import UploadFile
from ...data.uploader import Uploader
from ...utils.print import printer
from ..args import Google, Xai

config: SachmisConfig = get_config()


def main() -> None:
    app()


app = SafeTyper(
    name="files",
    help="Manage local files used for prompt attach",
)


@app.command()
def show(details: bool = False):
    """Show all files in camp registry"""
    forest: Forest = Forest.read_mode(config.paths.forest_file)
    camp: CampManager = forest.get_camp()
    base_name: str = config.paths.base_dir.stem

    if details:
        printer(camp.files)

    printer.title(f"Files in Camp of Base '{base_name}' {camp.files.n_files}")
    printer([file.local_path for file in camp.files.files])


@app.command()
def load(fresh: bool = False, files: sargs.Files = None):
    """Load local files from folder into camp registry"""

    printer("Not implemented, fresh: ", fresh)  # TODO: clear

    with Forest.edit_mode(config.paths.forest_file) as forest:
        camp: CampManager = forest.get_camp()
        printer(f"Files before: {len(camp.files.files)}")

        # FIX: panel stays empty (but works otherwise)
        new_files: list[UploadFile] = camp.prepare_and_load(files)
        printer.lines_with_len(
            name="New Loaded Files",
            lines=[file.local_path for file in new_files],
            style="purple",
        )

        printer.success(f"Attach Camp to {forest}")
        forest.attach_camp_back_by_mirror(camp)
        printer(f"Files after: {len(camp.files.files)}")


@app.command()
def online(xai: Xai = False, google: Google = False):
    """Show all files on remote registry"""

    uploader = Uploader(*_zero_is_all(xai, google))
    uploader.show_all_files()


@app.command()
def push(xai: Xai = False, google: Google = False, ensure=True):
    """Sync all files in Forest to remote registry"""

    uploader = Uploader(*_zero_is_all(xai, google))

    with Forest.edit_mode(config.paths.forest_file) as forest:
        camp: CampManager = forest.get_camp()

        registry_files: list[UploadFile] = camp.files.files
        printer(registry_files)

        uploaded_files: list[UploadFile] = uploader.load_files(
            registry_files, ensure_after_upload=ensure
        )
        printer(uploaded_files)

        logger.info(f"{len(registry_files)=}, {len(uploaded_files)=}")
        printer(camp.files.files)

        forest.attach_camp_back_by_mirror(camp)


@app.command()
def status(xai: Xai = False, google: Google = False):
    """Show remote status of all files in Forest"""

    uploader = Uploader(*_zero_is_all(xai, google))

    uploader.compare_with_remote_files(
        Forest.read_mode(config.paths.forest_file).files.files
    )


@app.command()
def clear(xai: Xai = False, google: Google = False):
    """Delete all files in remote registry"""

    uploader = Uploader(xai, google)  # No _zero_is_all!
    if not uploader.clients:
        printer.yellow("nothing to do...")
        return

    uploader_text: str = " and ".join(u.print_name for u in uploader.clients)

    text = f"All remote files on {uploader_text} will be deleted"
    printer.danger(text)

    if input("Are you sure? (type 'yes' to confirm): ") == "yes":
        uploader.delete_all_uploaded_files()
    else:
        printer.warn("Abandoned delete all files")


@app.command()
def delete():
    """Delete single file(s) in remote registry"""
    # TASK: create selection method
    # - xai just needs .id
    # - google just needs .name
    # - picker for all online/local files would work as well
    printer.danger("Not already implemented ")


def _zero_is_all(*args):  # MOVE: to args? latest at second usage
    """Modify input bool args only if all False -> all True"""
    return args if any(args) else (True for _ in args)
