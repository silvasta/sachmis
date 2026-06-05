from sstcore.cli.engine import SafeTyper
from sstcore.exceptions import TuiSelectorError
from sstcore.utils import printer

from sachmis.exceptions import ArborealFileError

from ..config import SachmisConfig, get_config
from ..exceptions import SachmisLaunchError
from . import command, subapp

config: SachmisConfig = get_config()


app = SafeTyper(
    name="sachmis",
    help="CLI for direct communication with LLMs",
    param=config.setup_info,
)


# core
# app.command()(command.thunder)
app.command()(command.fire)
# app.command()(command.tree)  # TASK: rename to sprout???
# app.command()(command.loop)

# utils
app.command()(command.init)
app.command("config")(command.config_details)
app.command("models")(command.model_display)
app.command()(command.rules)
# app.command()(command.roles)

# nested
app.add_typer(subapp.biome)
app.add_typer(subapp.forest)
# app.add_typer(subapp.tree) # NEXT: change to tree handler?
app.add_typer(subapp.files)
app.add_typer(subapp.utils)


@app.register_error(SachmisLaunchError)
def handle_arbo(error: SachmisLaunchError):
    printer.warn(f"{printer.colors.red('Problem!')} {error=}")


@app.register_error(TuiSelectorError)
def handle_tui_selector_error(error: TuiSelectorError):
    """Fails cleanly when an interactive selector UI is exited or aborted."""
    printer.warn(f"Interface canceled: {error}")


@app.register_error(ArborealFileError)
def handle_arboreal_file_error(error: ArborealFileError):
    """Standardized terminal fallback for structural I/O blocks."""
    printer.danger(f"Critical Arboreal I/O Error: {error}")
