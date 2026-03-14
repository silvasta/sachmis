import typer
from loguru import logger

from ..core.data import DataManager
from ..utils.log import logger_catch
from ..utils.print import printer


def main() -> None:
    app()


app = typer.Typer(
    name="forest",
    help="Local folder structure managed by Forest",
    no_args_is_help=True,
)


@app.callback()
def main_callback(ctx: typer.Context):
    printer.title(f"Welcome to {__name__}!", style="sub-title")


# TODO: sub-commands for forest:
# - compare master tree file with local nodes and edges
# - repair structure: recover, remove, replace.. or warn


@app.command()
@logger_catch
def tree(ctx: typer.Context):
    """Show forest structure as tree"""
    data: DataManager = ctx.obj["data"]
    data.show_forest(mode="tree")


@app.command()
@logger_catch
def file(ctx: typer.Context):
    """Show forest as print of master tree file"""
    data: DataManager = ctx.obj["data"]
    data.show_forest(mode="loaded")


if __name__ == "__main__":
    main()
