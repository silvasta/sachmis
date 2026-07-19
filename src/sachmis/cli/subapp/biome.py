from collections.abc import Callable
from pathlib import Path

from loguru import logger
from sstcore import SafeTyper, System, printer
from sstcore.exceptions import TuiSelectorError
from sstcore.tui import ListSelectorApp
from typer import Context

from sachmis.config import SachmisConfig

from ...cli import args
from ...data.arboreal import ArborealTracker, Biome
from .executor import BiomeExecutor


def main() -> None:
    app()


app = SafeTyper(
    name="biome",
    help="Biome - Home of Every Forest",
)


@app.command()
def setup(
    ctx: Context,
    name: args.Name = "",
):
    """Create new Biome with global data structure"""
    config: SachmisConfig = ctx.obj["config"]

    name: str = name or config.names.biome_file
    executor = BiomeExecutor()  # FIX:
    executor.execute(executor.create_new_biome, name)


@app.command()
def select(ctx: Context):
    """Show all Biome Files and select active Biome"""
    config: SachmisConfig = ctx.obj["config"]

    # MOVE: into BiomeExecutor
    _sst: System = ctx.obj["config"]
    executor = BiomeExecutor()

    def _select() -> Biome:
        biomes: list[Path] = list(config.paths.biome_files)
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
def show(ctx: Context):
    """Show all Biomes and load active Biome"""

    config: SachmisConfig = ctx.obj["config"]

    # MOVE: into BiomeExecutor
    _sst: System = ctx.obj["config"]
    executor = BiomeExecutor()
    biome: Biome = executor.execute(_load_operation(config))

    logger.info(f"Loaded {biome.n_forest=}, {biome.n_responses=}")

    print_all_biome_files(config)


def _load_operation(config: SachmisConfig) -> Callable[..., Biome]:
    def load():
        biome_file = config.paths.biome_file()
        return Biome.read_mode(biome_file)

    return load


@app.command("stat")
def arboreal_statistic(ctx: Context):
    """Show statistics of active Biome"""
    config: SachmisConfig = ctx.obj["config"]

    # MOVE: into BiomeExecutor
    _sst: System = ctx.obj["config"]
    executor = BiomeExecutor()

    biome: Biome = executor.execute(_load_operation(config))
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


def print_all_biome_files(config: SachmisConfig):
    printer.lines(
        lines=list(config.paths.biome_files),
        title="Selecting from Biome Files",
    )


if __name__ == "__main__":
    main()
