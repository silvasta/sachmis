from pathlib import Path

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
from ...exceptions import ArborealFileExistsError
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
    config: SachmisConfig = get_config()

    # REFACTOR: pick nice elements, delete rest
    try:
        biome: Biome = Biome.with_name(name)

    except ArborealFileExistsError as error:
        items: list[str] = [
            f"Failed to Load Biome... {printer.colorbox().red(str(error))}",
            "Check the provided location and choose an available name.",
            f"{error.file=}",
        ]
        printer(items, style="danger")
        raise

    items: list[str] = [
        f"Successfully Created {printer.green('New Biome')}!",
        f"{biome.tracker_info.stat=}",
    ]
    printer(items, style="success")

    printer.success("All Existing Biome Files")
    printer.lines(list(config.paths.biome_files), style="success")


@app.command()
def show():
    """Show all Biomes and load active Biome"""
    config: SachmisConfig = get_config()
    printer.success(f"{_b('BiomeDir')} {_path(config.paths.biome_dir)}")

    # TASK: this as master pipeline

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

    with Biome.observe(obsi=BiomeObserver.init()) as observer:
        # AI: here another try block?
        # TASK: from here: show, stat, setup. maybe injected or by arg/enum
        biome_file: Path = config.paths.biome_file()
        printer.success(f"{_b('Active Biome')} {_path(biome_file)}")

        biome: Biome = Biome.read_mode(biome_file)  # Maybe pipe trough class?
        logger.info(f"Biome Loaded {biome.n_forest=}, {biome.n_responses=}")
        # AI: if so, how to handle exceptions?
        # Is it still bubbling up to observe when I use this:
        # except ArborealFileMissingError:
        #     pass  # expected, handled in context

    # TASK: this as function depending on task
    # TODO: split below if needeed again
    match observer.result:
        case BiomeStatus.STARTED:
            raise RuntimeError
        case BiomeStatus.OK:
            printer.success("Biome Inspected Successfully")
        case BiomeStatus.FAIL_OBSERVE:
            printer.danger("Failed to read Biome... check the logs")
        case BiomeStatus.FAIL_CREATE:
            printer.danger("Failed to create Biome... check the logs")
        case BiomeStatus.CREATED:
            printer.success("Successfully created New Biome")
        case BiomeStatus.PROMPT:
            if n_biome > 0:
                if Confirm.ask("Do you want to switch Biome?"):
                    _select_biome_switch()
                elif Confirm.ask("Create new Biome?"):
                    pass  # NEXT:

    printer.panel("Biome Closed", frame="purple")


@app.command()
def select():
    """Show all Biome Files and select active Biome"""
    printer.lines(  # INFO: usually not visible (or lets say, after Selector)
        lines=(biomes := list(get_config().paths.biome_files)),
        title="Selecting from Biome Files",
    )
    _select_biome_switch(biomes)


# TASK: this is already nice, connect!
def _select_biome_switch(biomes: list[Path] | None = None):
    biomes: list[Path] = biomes or list(get_config().paths.biome_files)

    if not (select := ListSelectorApp(items=biomes, multi_select=False).run()):
        raise TuiSelectorError("Try better, Biomi is Important..!")

    printer.success(f"Selected: {(biome_file := Path(select[0])).name}")

    with Biome.edit_mode(biome_file) as biome:
        biome.apply_to_config(biome_file)
        biome.touch()


@app.command()
def stat():  # TASK: generic for Arbo
    """Show statistics of active Biome"""
    config: SachmisConfig = get_config()

    printer.md("This function is not on the current state...")
    active: str = "[bold]Active:[/]"
    printer.warn(f"{active} {config.paths.biome_file}")

    biome: Biome = Biome.read_mode(config.paths.biome_file())
    forests: list[ArborealTracker] = biome.forests

    to_print: list[str] = []  # NEXT: show forest
    for forest in forests:  # TODO: SimpleTree with nice statistics!
        name: str = forest.path.parent.parent.name
        to_print.append(f"[bold black on white]{name}[/] - {forest.path}")

    printer.lines_with_len(
        name="Forests",
        lines=to_print,
    )
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
