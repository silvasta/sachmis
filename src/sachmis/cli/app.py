from pathlib import Path

import typer
from silvasta.cli import monitor
from silvasta.cli.setup import attach_callback, logger_catch

from ..utils.print import printer

# TODO: create __init__ and load from there
from .command.fire import fire
from .command.loop import loop
from .command.thunder import thunder
from .command.tree import tree

# TODO: create __init__ and load from there
from .subapp.bases import app as bases_app
from .subapp.files import app as files_app
from .subapp.forest import app as forest_app
from .subapp.show import app as show_app


def main() -> None:
    printer.title("Welcome to sachmis!")
    app()


app = typer.Typer(
    name="sachmis",
    help="CLI for direct communication with LLMs",
    no_args_is_help=True,
)
attach_callback(app)


app.command()(fire)
app.command()(tree)
app.command()(loop)
app.command()(thunder)

app.add_typer(files_app)
app.add_typer(forest_app)
app.add_typer(bases_app)
app.add_typer(show_app)


@app.command("print")
@logger_catch
# MOVE: to command, some collector file
def print_file(path: Path):
    """Print prompt, answer or any Markdown file"""
    printer.md(path.read_text())


@app.command("monitor")
@logger_catch
# MOVE: to command, some collector file
def launch_monitor(file: Path | None = None):
    """Launch Log Console Monitor to display new arriving entries in log file"""
    monitor(log_path=file)


# @app.callback()
# def main_callback(
#     ctx: typer.Context,
#     verbose: bool = typer.Option(False, "--verbose", "-v", help="Show debug logs"),
#     quiet: bool = typer.Option(False, "--quiet", "-q", help="Disable terminal output"),
# ):
#     """Global setup for logging and data loading"""
#
#     # Logging for Typer CLI, works across different entry points
#     level: str | None = "DEBUG" if verbose else None
#     setup_logging(log_level_override=level, quiet=quiet)
#
# TODO: check together with .log.setup how and where to load data
#
#     # Single object for file system data and config
#     ctx.obj: dict[str, DataManager] = {"data": DataManager()}
#
#     # for debug  purposes in case somthing went wrong in the pipeline
#     if ctx.invoked_subcommand is not None:
#         logger.debug("Welcome to main_callback")


if __name__ == "__main__":
    main()
