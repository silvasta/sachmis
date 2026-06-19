from sstcore.cli import SafeTyper

from ..config.manager import config_loader
from ..utils import printer
from . import command, subapp
from .fire import fire
from .handlers import attach_handlers
from .thunder import thunder

app = SafeTyper(
    name="sachmis",
    help="CLI for direct communication with LLMs",
    config_loader=config_loader,
)

# core
# printer.warn("Thunder")
# printer.danger("Fire")
app.command()(thunder)
app.command()(fire)

# important
app.command()(command.init)

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


# TASK: where to place? DEBUG
app.add_typer(subapp.debug)
printer.project_debugs = True

attach_handlers(app)
