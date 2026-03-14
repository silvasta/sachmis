from typing import Annotated

import typer
from silvasta.cli.setup import attach_callback, logger_catch

from sachmis.core.data import DataManager
from sachmis.utils.print import printer


def main() -> None:
    printer.title(f"Welcome to {__name__}!", style="sub-title")
    app()


app = typer.Typer(
    name="base",
    help="Local base as home of forest",
    no_args_is_help=True,
)
attach_callback(app)


@app.callback()
def main_callback(ctx: typer.Context):
    """Global setup for sachmis"""
    printer.title(f"Welcome to {__name__}!", style="sub-title")


@app.command()
@logger_catch
def init(
    name: Annotated[
        str,
        typer.Option("--name", "-n"),
    ] = "base",
):
    """Create new base with data structure and local config"""
    data = DataManager()
    data.create_new_base(name)


@app.command()
@logger_catch
def list():
    """Global localization of all bases"""
    # NOTE: logging works, just some formating left
    # sub-commands for bases:
    # - list of path of all bases
    # - check if path exist, active bases
    # - check if file structure fine, fixable, broken, lost -> like forest() below
    # - maybe show statistics
    DataManager().show_all_bases()


if __name__ == "__main__":
    main()
