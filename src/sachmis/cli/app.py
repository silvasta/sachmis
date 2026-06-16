from sstcore.cli.engine import SafeTyper
from sstcore.exceptions import TuiSelectorError
from sstcore.utils import printer

from sachmis.exceptions import ArborealFileError

from ..config import SachmisConfig, get_config
from ..exceptions import SachmisLaunchError
from . import command, subapp
from .fire import fire
from .thunder import thunder

config: SachmisConfig = get_config()


app = SafeTyper(
    name="sachmis",
    help="CLI for direct communication with LLMs",
    param=config.setup_info,
)

# core
app.command()(thunder)
app.command()(fire)

# important
app.command()(command.init)
# app.command("roll")(command.rollout)

# utils
app.command("models")(command.model_display)
app.command()(command.rules)  # TODO: check
app.command("config")(command.config_details)

# nested
app.add_typer(subapp.files)
app.add_typer(subapp.biome)
app.add_typer(subapp.forest)
# app.add_typer(subapp.tree) # TASK: change to tree handler?
app.add_typer(subapp.utils)

if config.defaults.debug.subapp:
    app.add_typer(subapp.debug)

# TASK: Global Error Handling
# - SachmisDataError: confirm handled in DataManager
# - other globals?


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
