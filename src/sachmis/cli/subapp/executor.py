from enum import StrEnum, auto
from pathlib import Path

import typer
from rich.prompt import Confirm
from sstcore import System
from sstcore.tui import selector
from sstcore.utils import printer
from sstcore.utils.color import ColorBox

from ...config import Paths, SachmisConfig
from ...data.arboreal import ArborealTracker, Biome
from ...exceptions import ArborealTrackingError

c = ColorBox()


class _BiomeStatus(StrEnum):
    OK = auto()
    FAIL_CREATE = auto()
    CREATED = auto()
    PROMPT = auto()


class _BiomeTask(StrEnum):
    NEW = auto()
    SELECT = auto()
    SHOW = auto()


class DirStatus(StrEnum):
    ZERO = auto()
    ONE = auto()
    MULTI = auto()

    @classmethod
    def from_config(cls, paths: Paths) -> DirStatus:
        """Set with Path Information from _config.Paths"""
        match paths.n_biome_files:
            case 0:
                return cls.ZERO
            case 1:
                return cls.ONE
            case _:
                return cls.MULTI

    def print(self, paths: Paths):
        """Check global Biome Dir and show status"""
        text = f"{c.b('BiomeDir')} {(paths.biome_dir)}"
        printer.success(text)  # TODO: emit? probably just print
        match self:
            case self.ZERO:
                text = f"{c.red('Zero')} Biome Files found!"
                printer.danger(text)
            case self.ONE:
                text = f"{c.yellow('Only 1')} Biome File found!"
                printer.warn(text)
            case self.MULTI:
                text = f"{c.g(paths.n_biome_files)} Biome Files found!"
                printer.success(text)
                printer.lines(list(paths.biome_files))


class BiomeOperator:
    """Handle Biome Setup, Creation and Selection"""

    # LATER: ArborealOperator? common stuff for all Arbos, detailed wher needed
    # IDEA: split scroll/operation, cli/data.operator
    # - or keep in cli, move operation to arbos itself?
    # - box like log and _config at beginning? maybe even in printer as layout

    @property
    def _config(self) -> SachmisConfig:
        return self._system.config

    @property
    def _paths(self) -> Paths:
        return self._config.paths

    def __init__(self, sst: System):
        self._system: System = sst
        self._dir_status: DirStatus = DirStatus.from_config(self._paths)
        self._dir_status.print(self._paths)

    def create(self, name: str | None) -> Biome:
        """Create new Biome with global data structure"""
        try:
            biome: Biome = Biome.named(self._config, name)
            text = (f"Successfully Created {printer.green('New Biome')}!",)
            printer.success(text)
        except ArborealTrackingError as error:
            printer.danger("Biome with this Name already Exists!")
            printer(error.file)
            raise
            # TODO: ask for swithc?
        return biome

    def select(self):
        """Show all Biome Files and select active Biome"""
        match self._dir_status:
            case DirStatus.ZERO:
                self._ask_for_new()
            case DirStatus.ONE:
                # LATER: check if the 1 is actually set, otherwise ask?
                self._ask_for_new()
            case DirStatus.MULTI:
                biome_file: Path = selector.single_linear(
                    {path: path.name for path in self._paths.biome_files}
                )
                printer.success(f"Selected: {biome_file.name}")
                with Biome.edit_mode(biome_file) as biome:
                    biome.set_active(biome_file, self._config)
                    return biome

    def show(self):
        """Show all Biomes and active Biome"""
        match self._dir_status:
            case DirStatus.ZERO:
                self._ask_for_new()
            case DirStatus.MULTI | DirStatus.ONE:
                printer.lines(
                    lines=list(self._paths.biome_files),
                    title="All Biome Files",
                )
                active_biome: Path = self._paths.biome_file()
                printer.header(active_biome, title="Active Biome")

    def stat(self):
        """Show statistics of active Biome"""
        biome: Biome = Biome.read_mode(self._paths.biome_file())
        printer.header(text=self._paths.biome_file(), title="Active Biome")
        # WARN: loop for DirStatus.ONE, bad? ask for biome with new name
        forest_statistic(biome)

    def _ask_for_new(self):
        printer.warn("Action required to resolve Biome _configuration:")
        if Confirm.ask(c.magenta("Create a new Biome?")):
            name: str = typer.prompt("Enter new Biome name", default=None)
            return self.create(name)

    def _ask_for_switch(self):
        printer.warn("Action required to resolve Biome _configuration:")
        if Confirm.ask(c.magenta("Switch to an existing Biome?")):
            self.select()  # TEST: full self.select pipeline?


def forest_statistic(biome: Biome):
    forests: list[ArborealTracker] = biome.forests
    to_print: list[str] = []

    for forest in forests:
        name: str = forest.path.parent.parent.name
        # TODO: SimpleTree with nice statistics! - layout
        to_print.append(f"[bold black on white]{name}[/] - {forest.path}")

    printer.lines_with_len(name="Forests", lines=to_print)
    printer.path_exists_table([forest.path for forest in forests])
