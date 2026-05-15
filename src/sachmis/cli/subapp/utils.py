import typer
from sstcore.cli import logger_catch, utils_app

from ...data import DataManager
from ...utils.print import printer


def main() -> None:
    app()


app: typer.Typer = utils_app


@app.command()
@logger_catch
def data(biome: bool = False, forest: bool = False):
    """Open DataManger in Context: with DataManger() as data..."""

    with DataManager(biome, forest) as data:
        printer(vars(data))


if __name__ == "__main__":
    main()
