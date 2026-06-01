import os
import sys

import typer
from loguru import logger

IS_COMPLETION: bool = (  # TEST: is this actually useful/necessary?
    "_SACHMIS_COMPLETE" in os.environ
    or "--show-completion" in sys.argv
    or "--install-completion" in sys.argv
)

logger.remove()  # Intercept all logs

# Intercept logger to generate Typer auto-completion
if not IS_COMPLETION:
    _boot_handler = logger.add(sys.stderr, level="INFO")

from sstcore.cli import attach_callback  # noqa: E402

from ..config import SachmisConfig, get_config  # noqa: E402
from . import command, subapp  # noqa: E402

config: SachmisConfig = get_config()


def main():
    app()


# main
app = typer.Typer(
    name="sachmis",
    help="CLI for direct communication with LLMs",
    no_args_is_help=True,
)
attach_callback(app, param=config.setup_info)

# core
# app.command()(command.thunder)
app.command()(command.fire)
# app.command()(command.tree)  # TASK: rename to sprout???
# app.command()(command.loop)

# utils
app.command()(command.init)
app.command("config")(command.config_details)
app.command()(command.models)
app.command()(command.rules)
# app.command()(command.roles)

# nested
app.add_typer(subapp.biome)
app.add_typer(subapp.forest)
# app.add_typer(subapp.tree) # NEXT: change to tree handler?
app.add_typer(subapp.files)
app.add_typer(subapp.utils)


if __name__ == "__main__":
    main()
