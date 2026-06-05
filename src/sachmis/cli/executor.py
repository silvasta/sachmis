from collections.abc import Callable
from pathlib import Path
from typing import Any

import typer
from loguru import logger
from pydantic import BaseModel, ConfigDict
from rich.prompt import Confirm
from sstcore.tui import ListSelectorApp
from sstcore.utils import printer
from sstcore.utils.print import ColorBox

from ..config import SachmisConfig, get_config
from ..data.arboreal.biome import Biome, BiomeStatus
from ..exceptions import (
    ArborealFileExistsError,
    ArborealFileMissingError,
)

config: SachmisConfig = get_config()


class BiomeExecutor(BaseModel):
    """Orchestrates Biome operations, manages prompt loops, and enforces typed output."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    active_biome: Biome | None = None
    last_status: BiomeStatus = BiomeStatus.STARTED

    def execute(self, operation: Callable[..., Any], *args, **kwargs) -> Biome:
        """Executes a target biome action with unified safety wrappers and error state tracking."""
        self.last_status = BiomeStatus.STARTED
        self._print_directory_status()

        try:
            result = operation(*args, **kwargs)

            if isinstance(result, Biome):
                self.active_biome: Biome = result
                self.last_status = BiomeStatus.OK
                printer.success("Biome Operation Successful")
                return self.active_biome

            raise ValueError(
                f"Operation did not return a valid Biome instance: {result}"
            )

        except ArborealFileMissingError as err:
            logger.warning(f"Biome file missing: {err.file}")
            self.last_status = BiomeStatus.PROMPT
            return self._handle_interactive_fallback()

        except ArborealFileExistsError as err:
            logger.error(f"Target Biome already exists: {err.file}")
            self.last_status = BiomeStatus.FAIL_CREATE
            text = f"Failed to create {c.red(Biome)}. File conflict detected."
            printer.danger(text)
            return self._handle_interactive_fallback()

        except Exception:
            self.last_status = BiomeStatus.FAIL_OBSERVE
            logger.exception("Critical unexpected failure in Biome pipeline")
            raise typer.Exit(code=1) from None

    def _handle_interactive_fallback(self) -> Biome:
        """Handles interactive terminal fallbacks sequentially without deep stack recursion."""
        printer.warn("Action required to resolve Biome configuration:")

        # 1. Ask to Switch Biome if other biome files exist
        if config.paths.num_biome_files > 0:
            if Confirm.ask(c.magenta("Switch to an existing Biome?")):
                biomes: list[Path] = list(config.paths.biome_files)
                tui = ListSelectorApp(items=biomes, multi_select=False)
                if selected := tui.run():
                    biome_file = Path(selected[0])
                    printer.success(f"Selected: {biome_file.name}")
                    with Biome.edit_mode(biome_file) as b:
                        b.apply_to_config(biome_file)
                        b.touch()
                        self.active_biome = b
                        self.last_status = BiomeStatus.OK
                        return b
                else:
                    printer.danger("No selection made.")

            # 2. Ask to Create a New Biome
            if Confirm.ask(c.magenta("Create a new Biome?")):
                name: str = typer.prompt("Enter new Biome name", default=None)
                return self.create_new_biome(name)

        # 3. Fallback Creation Hook
        printer.success("Creating default Biome fallback...")
        return self.create_new_biome(None)

    def create_new_biome(self, name: str | None) -> Biome:
        """Isolated direct biome instantiation."""
        biome: Biome = Biome.with_name(name)
        self.active_biome: Biome = biome
        self.last_status = BiomeStatus.CREATED
        text = (f"Successfully Created {printer.green('New Biome')}!",)
        printer.success(text)
        return biome

    @staticmethod
    def _log_filesystem_status(cls) -> None:  # TODO: toggle
        config: SachmisConfig = get_config()
        logger.debug("start detecting")
        num_biome_files: int = config.paths.num_biome_files
        logger.debug(f"found {num_biome_files=} in {config.paths.biome_dir=}")
        biome_files: set[Path] = config.paths.biome_files
        logger.debug(f"current status: {biome_files=}")

    @staticmethod
    def _print_directory_status() -> None:  # TODO: toggle
        config: SachmisConfig = get_config()
        text = f"{_b('BiomeDir')} {_p(config.paths.biome_dir)}"
        printer.success(text)
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


c: ColorBox = printer.colorbox()


def _p(path: Path) -> str:
    """Render path by folder and file color split"""
    return printer._format(path)


def _b(text: str) -> str:
    """Short inline colorizing for Biome names with surrounding"""
    return c.green(text)
