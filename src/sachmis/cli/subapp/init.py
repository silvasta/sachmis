import typer
from silvasta.cli.setup import attach_callback, logger_catch

from sachmis.cli.args import Name
from sachmis.data import DataManager


def main() -> None:
    app()


# NEXT: with new arboreal

app = typer.Typer(
    name="init",
    help="Local base - Home of the Forest",  # TODO: naming
    no_args_is_help=True,
)
attach_callback(app)


@app.command()
@logger_catch
def biome(name: Name = ""):
    # LATER: setup multiple biomes? each with differnet name?
    """Create new biome with global data structure"""  # TODO: naming
    DataManager.create_new_biome(
        name
    )  # NEXT: why not automatic at first launch?


@app.command()
@logger_catch
def base(name: Name = "base"):
    """Create new base with forest and local data structure"""  # TODO: naming
    DataManager.create_new_base(name)


if __name__ == "__main__":
    main()
