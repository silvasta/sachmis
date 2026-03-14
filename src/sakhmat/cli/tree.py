import typer
from pathlib import Path

from ..core.data import DataManager
from ..utils.log import logger_catch
from ..utils.print import printer


# def main() -> None:
#     printer.title(f"Welcome to {__name__}!", style="sub-title")
#     app()
#
#
# app = typer.Typer(
#     name="tree",
#     help="Create new sprout at desired forest location",
#     no_args_is_help=True,
# )
#
#
# @app.callback()
# def main_callback(ctx: typer.Context):
#     """Global setup for sakhmat"""
#     printer.title(f"Welcome to {__name__}!", style="sub-title")
#
#
# @app.command()


@logger_catch
def tree(ctx: typer.Context, sprout: Path):
    """Create new sprout from existing response in new folder"""

    data: DataManager = ctx.obj["data"]
    data.load_forest()
    printer.title("Forest loaded, start creating new sprout")
    data.tree(sprout)


# if __name__ == "__main__":
#     main()
