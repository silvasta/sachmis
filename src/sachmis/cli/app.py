from pathlib import Path

import typer
from silvasta.cli import monitor
from silvasta.cli.setup import attach_callback, logger_catch

from ..utils.print import printer

from .command import (
    fire,
    loop,
    thunder,
    tree,
)

from .subapp import (
    bases_app,
    files_app,
    forest_app,
    show_app,
)


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
# - why not just in conductor at execution?
#   - specific setup per task
#   - overview of setup at 1 location
#   - no additional typer complexity, loss of type checks
#   - Minus: conductor forced to use it like that
#     - issue for later on TUI?
#     - issue for later on autonomous setup on Pi?
#
#     # Single object for file system data and config
#     ctx.obj: dict[str, DataManager] = {"data": DataManager()}
#
#     # for debug  purposes in case somthing went wrong in the pipeline
#     if ctx.invoked_subcommand is not None:
#         logger.debug("Welcome to main_callback")


if __name__ == "__main__":
    main()
