from pathlib import Path

import typer
from silvasta.cli.setup import attach_callback, logger_catch

from sachmis.core.data import DataManager
from sachmis.core.models import Geminis, Groks
from sachmis.utils.config import ConfigManager
from sachmis.utils.print import printer


def main() -> None:
    printer.title(f"Welcome to {__name__}!", style="sub-title")
    app()


app = typer.Typer(
    name="show",
    help="Show statistics, configurations and more",
    no_args_is_help=True,
)
attach_callback(app)


@app.callback()
def main_callback(ctx: typer.Context):
    printer.title(f"Welcome to {__name__}!", style="sub-title")


@app.command()
@logger_catch
def models():
    """Show all models of all providers"""
    # TODO: rich table, statistics
    printer.title(f"{Groks}")
    for model in Groks:
        printer.md(
            f"-x {model.value:<6} {model:<14} **{model.api_name}**",
            style="blue",
        )
    for model in Geminis:
        printer.md(
            f"-g {model.value:<6} {model:<14} **{model.api_name}**",
            style="green",
        )


@app.command()
@logger_catch
def usage(path: Path = Path.cwd(), all: bool = False):
    """Calculate usage of single conversatioon, {local|global} folder"""
    # TODO: CLI: show usage
    printer.fail("not avaliable")


@app.command()
@logger_catch
def config(ctx: typer.Context):
    """Print config to Console, so far just dotenv_path"""
    # TODO: show config:
    # - set some configs to show, pick or all?
    # - future, modify configs here or generate config files to modify
    data: DataManager = ctx.obj["data"]
    config: ConfigManager = data.config
    printer.print(f"{config.dotenv_path=}")


@app.command()
@logger_catch
def role(conversation_name):
    """Show and reate roles, stored {local|global}"""
    # TODO: create "new role" function
    printer.fail("not avaliable")


if __name__ == "__main__":
    main()
