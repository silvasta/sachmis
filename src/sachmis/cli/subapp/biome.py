from pathlib import Path

import typer
from loguru import logger
from sstcore.cli import attach_callback, logger_catch
from sstcore.exceptions import FailedSelectionError
from sstcore.tui import ListSelectorApp

from ...cli import args
from ...config import SachmisConfig, get_config
from ...data.arboreal import ArborealTracker, Biome
from ...exceptions import ArborealFileExistsError
from ...utils.print import printer


def main() -> None:
    app()


app = typer.Typer(
    name="biome",
    help="Biome - Home of Every Forest",
    no_args_is_help=True,
)
attach_callback(app)


@app.command()
@logger_catch
def setup(name: args.Name | None = None):
    """Create new Biome with global data structure"""
    config: SachmisConfig = get_config()

    try:
        biome: Biome = Biome.with_name(name)

    except ArborealFileExistsError as error:
        items: list[str] = [
            f"Failed to Load Biome... {printer.red(str(error))}",
            "Check the provided location and choose an available name.",
            f"{error.file=}",
        ]
        printer.scroll(items, style="danger")
        raise

    items: list[str] = [
        f"Successfully Created {printer.green('New Biome')}!",
        f"{biome.tracker_info.stat=}",
    ]
    printer.scroll(items, style="success")

    printer.success("All Existing Biome Files")
    printer.scroll(items=list(config.paths.biome_files), style="success")


@app.command()
@logger_catch
def show():
    """Show all Biomes and their Files"""
    config: SachmisConfig = get_config()

    Biome.check_filesystem()

    printer.danger("No Biome File found!")

    printer.warn("There is only 1 Biome File, nothing to select!")

    biome: Biome = Biome.read_mode(config.paths.biome_file)
    logger.info(f"Biome Loaded {biome.n_forest=}, {biome.n_responses=}")

    printer.success("All Existing Biome Files")
    printer.scroll(items=list(config.paths.biome_files), style="success")

    active: str = "[bold]Active:[/]"
    printer.title(f"{active} {config.paths.biome_file}", style="warning")


@app.command()
@logger_catch
def select():
    """Show all Biome Files and select active Biome"""
    config: SachmisConfig = get_config()

    printer.lines(
        lines=(biomes := list(config.paths.biome_files)),
        title="Selecting from Biome Files",
    )

    if not (select := ListSelectorApp(items=biomes, multi_select=False).run()):
        raise FailedSelectionError("Try better, Biomi is Important..!")

    printer.success(f"Selected: {(biome_file := Path(select[0])).name}")

    with Biome.edit_mode(biome_file) as biome:
        biome.apply_to_config(biome_file)
        biome.touch()


@app.command()
@logger_catch
def stat():  # LATER: generic for Arbo
    """Show statistics of active Biome"""
    config: SachmisConfig = get_config()

    printer.md("This function is not on the current state...")
    active: str = "[bold]Active:[/]"
    printer.title(f"{active} {config.paths.biome_file}", style="warning")

    biome: Biome = Biome.read_mode(config.paths.biome_file)
    forests: list[ArborealTracker] = biome.forests

    to_print: list[str] = []
    for forest in forests:  # TODO: SimpleTree with nice statistics!
        name: str = forest.path.parent.parent.name
        to_print.append(f"[bold black on white]{name}[/] - {forest.path}")

    printer.lines_with_len(
        name="Forests",
        lines=to_print,
    )
    printer.path_exists_table([forest.path for forest in forests])


if __name__ == "__main__":
    main()
