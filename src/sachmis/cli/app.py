from sstcore.cli.engine import SafeTyper

from ..config import SachmisConfig, get_config
from ..exceptions import SachmisLaunchError
from ..utils import printer
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
app.command()(command.config)
app.command()(command.models)
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
    printer.warn(f"{printer.red('Problem!')} {error=}")
