import opcode
import typer
from pathlib import Path
from loguru import logger

from ..core.data import DataManager
from ..utils.config import ConfigManager
from ..utils.log import logger_catch, setup_logging
from ..utils.print import printer
from .bases import app as bases_app
from .fire import fire
from .forest import app as forest_app
from .loop import loop
from .show import app as show_app
from .tree import tree
from .thunder import thunder
from .files import app as files_app


def main() -> None:
    printer.title("Welcome to sachmis!")
    app()


app = typer.Typer(
    name="sachmis",
    help="CLI for direct communication with LLMs",
    no_args_is_help=True,
)

# app.add_typer(loop_app)
# app.add_typer(fire_app)
# app.add_typer(tree_app)
app.add_typer(files_app)
app.add_typer(forest_app)
app.add_typer(bases_app)
app.add_typer(show_app)


app.command()(thunder)
app.command()(fire)
app.command()(tree)
app.command()(loop)


@app.command("print")
@logger_catch
def print_file(ctx: typer.Context, path: Path):
    """Print prompt, answer or any Markdown file"""
    printer.md(path.read_text())


@app.command()
@logger_catch
def hi(ctx: typer.Context):
    """Ping CLI and check if data and config is loaded"""
    printer.md("**CLI works** _hopefully_ with **Markdown**\n\n1,2, `test`")
    printer.md("TODO\n- finish the app!\n- Crush the exam 󰈸", H=2)
    printer.md("""
    ```python
    data: DataManager = ctx.obj["data"]
    config: ConfigManager = data.config
    ```
    """)
    data: DataManager = ctx.obj["data"]
    config: ConfigManager = data.config
    printer.print(config.project_root)
    printer.print(config.data_home)


@app.callback()
def main_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show debug logs"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Disable terminal output"),
):
    """Global setup for logging and data loading"""

    # Logging for Typer CLI, works across different entry points
    level: str | None = "DEBUG" if verbose else None
    setup_logging(log_level_override=level, quiet=quiet)

    # Single object for file system data and config
    ctx.obj: dict[str, DataManager] = {"data": DataManager()}

    # for debug  purposes in case somthing went wrong in the pipeline
    if ctx.invoked_subcommand is not None:
        logger.debug("Welcome to main_callback")


if __name__ == "__main__":
    main()
