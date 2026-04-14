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
def setup(name: Name = ""):  # REMOVE: not optional!
    # NEXT: create automatic at first launch
    # TASK: setup multiple biomes
    # - each with different name
    # - set default in settings.json
    """Create new Biome with global data structure"""
    DataManager.create_new_biome(name)


# TASK: commands
# - set active biome
# - show?
# - repair?
# - write all forest and trees to 1 folder?

if __name__ == "__main__":
    main()
