# sachmis/cli/handlers.py
from sstcore.cli import SafeTyper
from sstcore.exceptions import TuiSelectorError

from ..exceptions import ArborealFileError, SachmisLaunchError
from ..utils import printer


def attach_handlers(app: SafeTyper) -> None:
    """Binds all global error handlers to the CLI engine."""

    @app.register_error(SachmisLaunchError)
    def handle_launch(error: SachmisLaunchError):
        printer.warn(f"{printer.colors.red('Problem!')} {error=}")

    @app.register_error(TuiSelectorError)
    def handle_tui_selector(error: TuiSelectorError):
        printer.danger(f"Selector failed: {error}")

    @app.register_error(ArborealFileError)
    def handle_arboreal_file(error: ArborealFileError):
        printer.danger(f"Critical Arboreal I/O Error: {error}")
