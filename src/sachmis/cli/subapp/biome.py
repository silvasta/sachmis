from pathlib import Path

from loguru import logger
from sstcore.cli import SafeTyper
from sstcore.exceptions import TuiSelectorError
from sstcore.tui import ListSelectorApp
from sstcore.utils.print import ColorBox

from ...cli import args
from ...config import get_config
from ...data.arboreal import ArborealTracker, Biome
from ...data.arboreal.executor import BiomeExecutor
from ...utils.print import printer


def main() -> None:
    app()


app = SafeTyper(
    name="biome",
    help="Biome - Home of Every Forest",
)


@app.command()
def setup(name: args.Name = ""):
    """Create new Biome with global data structure"""
    name: str = name or get_config().names.biome_file
    executor = BiomeExecutor()
    executor.execute(executor.create_new_biome, name)


@app.command()
def select():
    """Show all Biome Files and select active Biome"""
    executor = BiomeExecutor()

    def _select() -> Biome:
        biomes: list[Path] = list(get_config().paths.biome_files)
        tui = ListSelectorApp(items=biomes, multi_select=False)

        if not (selected := tui.run()):
            raise TuiSelectorError

        biome_file = Path(selected[0])
        with Biome.edit_mode(biome_file) as biome:
            biome.apply_to_config(biome_file)
            biome.touch()
            return biome

    executor.execute(_select)


@app.command()
def show():
    """Show all Biomes and load active Biome"""
    executor = BiomeExecutor()

    biome: Biome = executor.execute(_load)
    logger.info(f"Biome Loaded {biome.n_forest=}, {biome.n_responses=}")
    print_all_biome_files()


def _load() -> Biome:
    config = get_config()
    biome_file = config.paths.biome_file()
    return Biome.read_mode(biome_file)


@app.command("stat")
def arboreal_statistic():
    """Show statistics of active Biome"""
    executor = BiomeExecutor()

    biome: Biome = executor.execute(_load)
    printer.success(f"Loaded Biome: {biome.tracker}")
    forest_statistic(biome)


# ==================== PRINT HELPERS ====================


def forest_statistic(biome: Biome):
    forests: list[ArborealTracker] = biome.forests
    to_print: list[str] = []

    # TODO: SimpleTree with nice statistics! - layout
    for forest in forests:
        name: str = forest.path.parent.parent.name
        to_print.append(f"[bold black on white]{name}[/] - {forest.path}")

    printer.lines_with_len(name="Forests", lines=to_print)
    printer.path_exists_table([forest.path for forest in forests])


def print_all_biome_files():
    printer.lines(
        lines=list(get_config().paths.biome_files),
        title="Selecting from Biome Files",
    )


c: ColorBox = printer.colorbox()


def _path(path: Path) -> str:
    """Render path by folder and file color split"""
    return printer._format(path)


def _b(text: str) -> str:
    """Short inline colorizing for Biome names with surrounding"""
    return c.green(text)


if __name__ == "__main__":
    main()
