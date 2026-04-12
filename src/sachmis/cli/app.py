import sys

import typer
from loguru import logger

logger.remove()  # Intercept until logging setup is done
_boot_handler = logger.add(sys.stderr, level="INFO")

from silvasta.cli import attach_callback

from sachmis.cli import command, subapp
from sachmis.config import SachmisConfig, get_config

config: SachmisConfig = get_config()


def main():
    app()


# main
app = typer.Typer(
    name="sachmis",
    help="CLI for direct communication with LLMs",
    no_args_is_help=True,
)
attach_callback(app, param=config.compose_setup_param())

# core
# app.command()(command.thunder)
app.command()(command.fire)
app.command()(command.tree)  # NEXT: rename to sprout???
# app.command()(command.loop)

# utils
app.command()(command.init)
app.command()(command.data)  # REMOVE: just for testing
app.command("print")(command.print_file)
app.command("monitor")(command.launch_monitor)

# nested
app.add_typer(subapp.biome)  # IDEA: or make this as setup, the 2 below to show
# app.add_typer(subapp.forest) # IMPORTANT: create forest handler
# app.add_typer(subapp.tree) # IMPORTANT: change to tree handler?
app.add_typer(subapp.files)
app.add_typer(subapp.show)


if __name__ == "__main__":
    main()
