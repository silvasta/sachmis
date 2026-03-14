import typer
from loguru import logger

from typing import Annotated
from ..core.data import DataManager
from ..utils.log import logger_catch
from ..utils.print import printer
from ..core.uploader import XaiUploader


def main() -> None:
    app()


app = typer.Typer(
    name="files",
    help="Local supporting file management",
    no_args_is_help=True,
)


@app.callback()
def main_callback(ctx: typer.Context):
    printer.title(f"Welcome to {__name__}!", style="sub-title")


@app.command()
@logger_catch
def load(ctx: typer.Context, fresh: bool = False, sort="simple"):
    """Load files from camp folder into file registry"""
    data: DataManager = ctx.obj["data"]
    data.load_files_to_forest(fresh, sort)


@app.command()
@logger_catch
def order(ctx: typer.Context):
    """Show files and status inside file registry"""
    data: DataManager = ctx.obj["data"]
    data.show_forest("order")


@app.command()
@logger_catch
def show(
    ctx: typer.Context,
    cat: list[str] | None = None,
    topic: list[str] | None = None,
):
    """Show files and status inside file registry"""
    data: DataManager = ctx.obj["data"]
    select: dict[str, list[str]] = {}

    if cat is not None:
        select["category"] = cat
    if topic is not None:
        select["topic"] = topic

    data.show_forest("files", select)


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
    printer.title("All online files will be deleted", style="bold white on red")

    if input("Are you sure? (type 'yes' to confirm): ") == "yes":
        data: DataManager = ctx.obj["data"]
        data.manage_online_forest_files(xai, google, task="delete")
    else:
        logger.warning("Abandoned delete all files")


if __name__ == "__main__":
    main()
