from pathlib import Path

import typer
from loguru import logger
from rich.prompt import Confirm
from sstcore.cli import SafeTyper
from sstcore.exceptions import TuiSelectorError
from sstcore.tui import ListSelectorApp
from sstcore.utils.print import ColorBox

from ...cli import args
from ...config import SachmisConfig, get_config
from ...data.arboreal import ArborealTracker, Biome
from ...data.arboreal.biome import BiomeObserver, BiomeStatus
from ...utils.print import printer


def main() -> None:
    app()


app = SafeTyper(
    name="biome",
    help="Biome - Home of Every Forest",
)


@app.command()
def setup(name: args.Name | None = None):
    """Create new Biome with global data structure"""
    main_biome_execution(create_biome, name)


@app.command()
def show():
    """Show all Biomes and load active Biome"""
    biome: Biome = main_biome_execution(load_file_and_biome)
    print_all_biome_files()
    logger.info(f"Biome Loaded {biome.n_forest=}, {biome.n_responses=}")


@app.command()
def select():
    """Show all Biome Files and select active Biome"""
    main_biome_execution(select_biome_switch)


@app.command("stat")
def arboreal_statistic():
    """Show statistics of active Biome"""
    biome: Biome = main_biome_execution(load_file_and_biome)
    forest_statistic(biome)


# ==================== CORE PIPELINE ====================


def main_biome_execution(func, *args):
    """Core of the module, every task pipes at least 1 function trough"""
    file_statistic()
    func_result = None

    observer = BiomeObserver.init()

    with Biome.observe(obsi=observer):
        func_result = func(*args)

    logger.debug(f"{observer=}")
    return result_dispatch(func_result, observer)


def result_dispatch(func_result, observer: BiomeObserver):
    logger.debug(f"{func_result=}")
    logger.debug(f"{observer=}")

    match observer.result:
        case BiomeStatus.STARTED:
            raise RuntimeError("Observer never completed!")

        case BiomeStatus.OK:
            if isinstance(func_result, Biome):
                printer.success(f"{_b('Biome')} Operation Successful")
                return func_result

        case BiomeStatus.FAIL_OBSERVE:
            printer.danger(f"Failed to load {_b('Biome')}... check the logs")
            typer.Exit(1)

        case BiomeStatus.FAIL_CREATE:
            printer.danger(f"Failed to create {_b('Biome')}... check the logs")
            print_for_fail_create()
            return _ask_user()

        case BiomeStatus.CREATED:
            if isinstance(func_result, Biome):
                printer.success(f"Successfully created New {_b('Biome')}")
                return func_result

        case BiomeStatus.PROMPT:
            return _ask_user()

    printer.panel(f"{_b('Biome')} Closed", frame="purple")


# ==================== USER INTERACTION ====================


def _ask_user() -> Biome | None:
    """Handle PROMPT / FAIL_CREATE cases"""
    config: SachmisConfig = get_config()

    if config.paths.num_biome_files > 0:
        if Confirm.ask("Do you want to switch Biome?"):
            return show()
        elif Confirm.ask("Create new Biome?"):
            name = typer.prompt("Biome name", default=None)
            return setup(name)

    # Fallback: create
    return setup(None)


# ==================== CORE OPERATIONS ====================
def create_biome(name) -> Biome:
    biome: Biome = Biome.with_name(name)
    print_created_biome(biome)
    return biome


def load_file_and_biome() -> Biome:
    biome_file: Path = _get_biome_file_path()
    biome: Biome = _read_biome_from_file(biome_file)
    print_loaded_biome(biome)
    return biome


def _get_biome_file_path() -> Path:
    config: SachmisConfig = get_config()
    biome_file: Path = config.paths.biome_file()
    printer.success(f"{_b('Active Biome')} {_path(biome_file)}")
    return biome_file


def _read_biome_from_file(biome_file: Path) -> Biome:
    return Biome.read_mode(biome_file)


def select_biome_switch(biomes: list[Path] | None = None):
    biomes: list[Path] = biomes or list(get_config().paths.biome_files)

    if not (select := ListSelectorApp(items=biomes, multi_select=False).run()):
        raise TuiSelectorError("Try better, Biomi is Important..!")

    printer.success(f"Selected: {(biome_file := Path(select[0])).name}")

    with Biome.edit_mode(biome_file) as biome:
        biome.apply_to_config(biome_file)
        biome.touch()


# ==================== PRINT HELPERS ====================


def file_statistic():
    config: SachmisConfig = get_config()
    printer.success(f"{_b('BiomeDir')} {_path(config.paths.biome_dir)}")
    match n_biome := config.paths.num_biome_files:
        case 0:
            text = f"{c.red('Zero')} Biome Files found!"
            printer.danger(text)
        case 1:
            text = f"{c.yellow('Only 1')} Biome File found!"
            printer.warn(text)
        case _:
            text = f"{c.green(n_biome)} Biome Files found!"
            printer.success(text)
            printer.lines(list(config.paths.biome_files))


def print_created_biome(biome):
    items: list[str] = [
        f"Successfully Created {printer.green('New Biome')}!",
        f"{biome.tracker_info.stat=}",
    ]
    printer(items, style="success")


def print_loaded_biome(biome: Biome):
    """Better name than print_created_biome"""
    printer.success(f"Loaded Biome: {biome.tracker_info.stat}")


def print_all_biome_files():
    printer.lines(
        lines=list(get_config().paths.biome_files),
        title="Selecting from Biome Files",
    )


def print_for_fail_create():
    printer.danger(
        "Failed to Load/Create Biome. Check the provided location and name."
    )


def forest_statistic(biome: Biome):
    forests: list[ArborealTracker] = biome.forests
    to_print: list[str] = []

    for forest in forests:  # TODO: SimpleTree with nice statistics! - layout
        name: str = forest.path.parent.parent.name
        to_print.append(f"[bold black on white]{name}[/] - {forest.path}")

    printer.lines_with_len(name="Forests", lines=to_print)
    printer.path_exists_table([forest.path for forest in forests])


c: ColorBox = printer.colorbox()


def _path(path: Path) -> str:
    """Render path by folder and file color split"""
    return printer._format(path)


def _b(text: str) -> str:
    """Short inline colorizing for Biome names with surrounding"""
    return c.green(text)


if __name__ == "__main__":
    main()
