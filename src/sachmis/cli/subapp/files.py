from itertools import product
from pathlib import Path

import typer
from silvasta.cli import attach_callback, logger_catch

from sachmis.cli.args import Google, Xai
from sachmis.config import SachmisConfig, get_config
from sachmis.data import DataManager
from sachmis.data.files import UploadFile
from sachmis.data.uploader import GoogleUploader, XaiUploader
from sachmis.data.uploader.uploader import FileUploader
from sachmis.utils.print import printer

# MOVE:
config: SachmisConfig = get_config()


def main() -> None:
    app()


app = typer.Typer(
    name="files",
    help="Manage local files used for prompt attach",
    no_args_is_help=True,
)
attach_callback(app)


@app.command()
@logger_catch
def load(fresh: bool = False):
    """Load files from local folder into file registry and camp folder"""
    # NEXT: data: setup for Forest, arborefactor
    # TASK: silvasta.data.FolderScanner
    with DataManager(forest_required=True) as data:
        data.load_local_files_to_forest(clear_current_files=fresh)


@app.command()
@logger_catch
def local():
    """Show all local files in Forest"""
    # NEXT: data: setup for Forest, arborefactor
    # TODO:  filter and display desired info

    with DataManager(forest_required=True, save_at_exit=False) as data:
        files: list[UploadFile] = data.forest.files

    printer.lines_from_list(
        lines=[file.description for file in files],
        header=f"Files in Base '{config.paths.base_dir.stem}': {len(files)}",
        title=f"{config.paths.base_dir}",
    )


@app.command()
@logger_catch
def push(xai: Xai = False, google: Google = False, ensure=True):
    """Sync all files in Forest to remote registry"""
    # NEXT: data: setup for Forest, arborefactor

    uploaders: list[FileUploader] = _prepare_uploader(xai, google)

    with DataManager(forest_required=True) as data:
        files: list[UploadFile] = data.forest.files
        for uploader, file in product(uploaders, files):
            uploader.upload_local_file(file, ensure_after_upload=ensure)


@app.command()
@logger_catch
def online(xai: Xai = False, google: Google = False):
    """Show all files on remote registry"""

    uploaders: list[FileUploader] = _prepare_uploader(
        *_zero_is_all(xai, google)
    )
    for uploader in uploaders:
        uploader.show_all_files()


@app.command()
@logger_catch
def status(xai: Xai = False, google: Google = False):
    """Show remote status of all files in Forest"""

    uploaders: list[FileUploader] = _prepare_uploader(
        *_zero_is_all(xai, google)
    )
    with DataManager(forest_required=True, save_at_exit=False) as data:
        local_files: list[UploadFile] = data.forest.files

    for uploader in uploaders:
        uploader.compare_with_remote_files(local_files)


@app.command()
@logger_catch
def clear(xai: Xai = False, google: Google = False):
    """Delete all files in remote registry"""

    uploaders: list[FileUploader] = _prepare_uploader(
        xai, google, forest_required=False
    )
    uploader_text: str = " and ".join(u.print_name for u in uploaders)

    text = f"All remote files on {uploader_text} will be deleted"
    printer.title(text, style="bold white on red")

    if input("Are you sure? (type 'yes' to confirm): ") == "yes":
        for uploader in uploaders:
            uploader.delete_all_uploaded_files()
    else:
        printer.warn("Abandoned delete all files")


@app.command()
@logger_catch
def delete():
    """Delete single file(s) in remote registry"""
    # TASK: create selecton method
    # - xai just needs .id
    # - google just needs .name
    # - picker for all online/local files would work as well
    printer.danger("Not already implemented ")


def _zero_is_all(*args):  # MOVE: to args? latest at second usage
    """Modify input bool args only if all False -> all True"""
    return args if any(args) else (True for _ in args)


def _prepare_uploader(
    xai: Xai = False, google: Google = False, forest_required=True
) -> list[FileUploader]:

    # Default path in FileUploader works only if cwd in_base
    local_dir: list = [] if config.paths.in_base else [Path.cwd()]
    if forest_required and local_dir:
        raise FileNotFoundError(f"No Forest found around cwd: {local_dir}")

    uploaders: list[FileUploader] = []

    uploaders += [XaiUploader(*local_dir)] if xai else []
    uploaders += [GoogleUploader(*local_dir)] if google else []

    if not uploaders:
        raise ValueError("No remote platform selected!")

    return uploaders


if __name__ == "__main__":
    main()
