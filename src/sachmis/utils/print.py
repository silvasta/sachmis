from itertools import cycle

from rich.table import Table
from sstcore.utils import Printer


class SachmisPrinter(Printer):
    def conversation_transition_result(
        self, prompt: str, response: str, result: bool, from_prompt: bool
    ):
        source = f"Prompt {self.colors.cyan(prompt)}"
        target = f"Response {self.colors.magenta(response)}"

        if not from_prompt:
            target, source = source, target

        text = f"{source} --> {target}"

        if result:
            self.success(text)
        else:
            self.danger(text)

    def model_table(
        self,
        uniques: list[str],
        names: list[str],
        api_names: list[str],
        title=None,
        show_header=True,
    ):
        """load base paths from file, check existence, print result"""

        printer.title("Table with all Active Models")
        table = Table(
            title=title,
            show_header=show_header,
            expand=True,
            border_style="cyan",
        )
        table.add_column("Unique")
        table.add_column("Name")
        table.add_column("API Request Alias")

        colors: list[str] = ["cyan", "magenta", "yellow", "green", "white"]

        for unique, name, api, color in zip(
            uniques, names, api_names, cycle(colors), strict=False
        ):
            table.add_row(unique, name, api, style=color)

        self(table)


printer = SachmisPrinter()
