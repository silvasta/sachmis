from itertools import cycle

from rich.table import Table
from sstcore.utils import Printer

from sachmis.config.model import ModelFamily

custom_theme: dict[str, str] = {
    # "write": "bold white on green",
    # LATER: now everything gone... what could be added?
}


class SachmisPrinter(Printer):
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
