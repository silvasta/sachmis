import typer
from silvasta.cli.setup import attach_callback, logger_catch

from sachmis.cli.args import Name
from sachmis.data import DataManager


def main() -> None:
    app()


app = typer.Typer(
    name="biome",
    help="Biome - Home of every Forest",
    no_args_is_help=True,
)
attach_callback(app)


@app.command()
@logger_catch
# NEXT: why not automatic at first launch?
def setup(name: Name = ""):
    # LATER: setup multiple biomes? each with differnet name?
    """Create new Biome with global data structure"""
    DataManager.create_new_biome(name)


if __name__ == "__main__":
    main()
