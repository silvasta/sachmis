# sachmis/cli/handlers.py
from sstcore import printer
from sstcore.cli import SafeTyper
from sstcore.exceptions import TuiSelectorError

from ..exceptions import ArborealError, SachmisLaunchError


def attach_exception_handlers(app: SafeTyper) -> None:
    """Binds all global error handlers to the CLI engine."""

    # TODO: bind proper ErrorHandler to SafeTyper with Bus connection

    @app.errors.handle()
    def handle_launch(error: SachmisLaunchError):
        printer.warn(f"{printer.color_box.red('Problem!')} {error=}")

    @app.errors.handle()
    def handle_tui_selector(error: TuiSelectorError):
        printer.danger(f"Selector failed: {error}")

    @app.errors.handle()
    def handle_arboreal_file(error: ArborealError):
        printer.danger(f"Critical Arboreal I/O Error: {error}")
