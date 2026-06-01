from itertools import cycle

from rich.table import Table
from sstcore.utils import Printer

custom_theme: dict[str, str] = {
    # "write": "bold white on green",
    # LATER: now everything gone... what could be added?
}


class SachmisPrinter(Printer):
    def show_conversation_transition_result(self, source: str, target: str):
        text = f"{self.cyan(source)} --> {self.magenta(target)}"
        self.header(text)
        self.success(text)
        self.danger(text)

    def model_table(
        self,
        model_uniques: list[str],
        model_api_names: list[str],
        title=None,
        show_header=True,
    ):
        """load base paths from file, check existence, print result"""

        table = Table(title=title, show_header=show_header)
        table.add_column("Unique")
        table.add_column("Name")
        table.add_column("API Request Alias")

        colors: list[str] = ["cyan", "magenta", "yellow", "green", "white"]

        for name, api, color in zip(
            model_uniques, model_api_names, cycle(colors), strict=False
        ):
            table.add_row(name, api, style=color)

        self(table)


printer = SachmisPrinter(custom_theme)
