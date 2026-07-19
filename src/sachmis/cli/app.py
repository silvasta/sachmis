from sstcore.cli import SafeTyper, tools
from sstcore.system.core import sst_system_loader

from ..config import config_loader
from . import command, subapp
from .fire import fire
from .handlers import attach_exception_handlers
from .thunder import thunder

app = SafeTyper(
    name="sachmis",
    help="CLI for direct communication with LLMs",
    system_loader=sst_system_loader(config_loader()),
)

# core
app.command()(thunder)
app.command()(fire)

# important
app.command()(command.init)

# utils
app.command("models")(command.model_display)
app.command("config")(command.config_details)

# nested
app.add_typer(subapp.files)
app.add_typer(subapp.biome)
app.add_typer(subapp.forest)
app.add_typer(tools)


app.add_typer(subapp.debug)  # NOTE: where to place? DEBUG

attach_exception_handlers(app)

app.system.printer.success("Handler Attached to SafeTyper")
