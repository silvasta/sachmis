from pathlib import Path

import typer
from loguru import logger
from sstcore.cli import attach_callback, logger_catch
from sstcore.tui import ListSelectorApp

from ...cli import args
from ...config import SachmisConfig, get_config
from ...data.arboreal import ArborealTracker, Biome
from ...data.setup import create_new_biome
from ...exceptions import ArborealFileMissingError
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
    biome_file: Path = create_new_biome(name)

    config.names.biome_file: str = biome_file.name
    config.save_settings()  # MOVE: 3er block to config?
    logger.info(f"Updated active Biome in Names: {biome_file=}")


@app.command()
@logger_catch
def show():
    """Show all Biomes and their Files"""
    config: SachmisConfig = get_config()
    printer.lines_with_len(
        name="Biomes",
        lines=list(config.paths.biome_files),
    )
    active: str = "[bold]Active:[/]"
    printer.title(f"{active} {config.paths.biome_file}", style="warning")


@app.command()
@logger_catch
def select():
    """Show all Biome Files and select 1"""
    config: SachmisConfig = get_config()
    biome_files: list[Path] = list(config.paths.biome_files)
    printer.lines(
        lines=biome_files,
        header=None,
        title="Selecting from Biome Files",
        style="cyan",
    )
    # MERGE: with check_biome_files
    match len(biome_files):
        case 0:
            printer.danger("No Biome File found!")
            raise ArborealFileMissingError("Biome", config.paths.biome_dir)
        case 1:
            printer.warn("There is only 1 Biome File, nothing to select!")
            printer(config.paths.biome_file)
            return
        case _:
            pass
    tui = ListSelectorApp(items=biome_files, multi_select=False)

    if not (selected := tui.run()):
        printer.warn("Action cancelled by user.")
        return
    biome_file: Path = Path(selected[0])

    printer.success(f"Selected {biome_file}")

    config.names.biome_file: str = biome_file.name
    config.save_settings()  # MOVE: 3er block to config?
    logger.info(f"Updated active Biome in Names: {biome_file.name=}")


@app.command()
@logger_catch
def stat():
    """Show statistics of active Biome"""
    # LATER: generic for Arbo
    config: SachmisConfig = get_config()

    active: str = "[bold]Active:[/]"
    printer.title(f"{active} {config.paths.biome_file}", style="warning")

    biome: Biome = Biome.read_mode(config.paths.biome_file)
    forests: list[ArborealTracker] = biome.forests

    to_print: list[str] = []
    for forest in forests:
        # TODO: SimpleTree with nice statistics!
        name: str = forest.path.parent.parent.name
        to_print.append(f"[bold black on white]{name}[/] - {forest.path}")

    printer.lines_with_len(
        name="Forests",
        lines=to_print,
    )
    printer.path_exists_table([forest.path for forest in forests])


# TASK: more commands:
# - repair?
# - write all forest and trees to 1 folder?

if __name__ == "__main__":
    main()
