from itertools import cycle
from pathlib import Path

from rich.table import Table
from sstcore.utils import Printer

from sachmis.config.model import ModelFamily

custom_theme: dict[str, str] = {
    # "write": "bold white on green",
    # LATER: now everything gone... what could be added?
}


class SachmisPrinter(Printer):
    def path_exists_table(self, paths: list[Path], title=None, header="Path"):
        """load base paths from file, check existence, print result"""

        # NEXT: candidate for silvasta.printer

        table = Table(title=title)
        table.add_column("Status", justify="center")
        table.add_column(header, style="cyan")

        for path in paths:
            status: str = "✅" if path.exists() else ""
            table.add_row(status, str(path))

        self(table)

    def model_table(
        self, models: list[ModelFamily], title=None, show_header=True
    ):
        """load base paths from file, check existence, print result"""

        table = Table(title=title, show_header=show_header)
        table.add_column("Unique")
        table.add_column("Name")
        table.add_column("API Request Alias")

        colors: list[str] = ["cyan", "magenta", "yellow", "green", "white"]

        for model, color in zip(models, cycle(colors), strict=False):
            table.add_row(
                model.unique, str(model), model.api_name, style=color
            )

        self(table)


printer = SachmisPrinter(custom_theme)
