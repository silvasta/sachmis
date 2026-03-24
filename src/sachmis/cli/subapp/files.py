from typing import Annotated

import typer
from loguru import logger
from silvasta.cli.setup import attach_callback, logger_catch

from sachmis.data import DataManager
from sachmis.data.uploader import XaiUploader
from sachmis.utils.print import printer


def main() -> None:
    app()


app = typer.Typer(
    name="files",
    help="Local supporting file management",
    no_args_is_help=True,
)
attach_callback(app)


@app.command()
@logger_catch
def load(clear: bool = False, sort="NotImplemented"):
    """Load files from camp folder into file registry"""
    with DataManager() as data:
        data.load_local_files_to_forest(clear_current_files=clear)


@app.command()
@logger_catch
def order(ctx: typer.Context):
    """Show files and status inside file registry"""
    data: DataManager = ctx.obj["data"]
    data.show_forest("order")


@app.command()
@logger_catch
def push(
    ctx: typer.Context,
    xai: Annotated[
        bool,
        typer.Option(
            "-x",
            help="Upload files to xAI file registry",
        ),
    ] = False,
    google: Annotated[
        bool,
        typer.Option(
            "-g",
            help="Upload files to Google file registry",
        ),
    ] = False,
):
    """Push files to online registry, needed for prompt!"""
    data: DataManager = ctx.obj["data"]
    data.manage_online_forest_files(xai, google, task="push")


@app.command()
@logger_catch
def online(
    ctx: typer.Context,
    xai: Annotated[
        bool,
        typer.Option(
            "-x",
            help="Upload files to xAI file registry",
        ),
    ] = False,
    google: Annotated[
        bool,
        typer.Option(
            "-g",
            help="Upload files to Google file registry",
        ),
    ] = False,
):
    """files overview from online registry"""
    data: DataManager = ctx.obj["data"]
    data.manage_online_forest_files(xai, google, task="show")


@app.command()
@logger_catch
def xf(ctx: typer.Context, delete: bool = False):
    """Compare local file status with status on xAI"""
    data: DataManager = ctx.obj["data"]
    data.load_forest()
    x = XaiUploader()
    if delete:
        x.delete_not_in_list(data.forest.files)
    x.compare_with_list(data.forest.files)


@app.command()
@logger_catch
def clear(
    ctx: typer.Context,
    xai: Annotated[
        bool,
        typer.Option(
            "-x",
            help="Upload files to xAI file registry",
        ),
    ] = False,
    google: Annotated[
        bool,
        typer.Option(
            "-g",
            help="Upload files to Google file registry",
        ),
    ] = False,
):
    """Delete files from online registry"""
    printer.title(
        "All online files will be deleted", style="bold white on red"
    )

    if input("Are you sure? (type 'yes' to confirm): ") == "yes":
        data: DataManager = ctx.obj["data"]
        data.manage_online_forest_files(xai, google, task="delete")
    else:
        logger.warning("Abandoned delete all files")


if __name__ == "__main__":
    main()
