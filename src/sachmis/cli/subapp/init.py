import typer
from silvasta.cli.setup import attach_callback, logger_catch

from sachmis.cli.args import Name
from sachmis.data import DataManager
from sachmis.utils.print import printer


def main() -> None:
    printer.title(f"Welcome to {__name__}!", style="sub-title")
    app()


app = typer.Typer(
    name="init",
    help="Local base - Home of the Forest",
    no_args_is_help=True,
)
attach_callback(app)


@app.command()
@logger_catch
def biome(name: Name = ""):
    # LATER: setup multiple biomes? each with differnet name?
    """Create new biome with global data structure"""
    DataManager.create_new_biome(name)


@app.command()
@logger_catch
def base(name: Name = "base"):
    """Create new base with forest and local data structure"""
    DataManager.create_new_base(name)


if __name__ == "__main__":
    main()
