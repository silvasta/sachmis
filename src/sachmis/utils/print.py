from itertools import cycle

from rich.table import Table
from sstcore.utils import Printer


class SachmisPrinter(Printer):
    def debug(self, title: str, *lines, bare=False):
        self.title(
            title,
            title="debug print",
            frame="orange_red1",
        )
        if not bare:
            self(lines)
        else:
            for line in lines:
                self.title(
                    str(line),
                    title="debug print",
                    frame="navajo_white1",
                )
                self(line)
        input(f"ENTER: {title}")

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
        header: str = "Table with all Active Models",
        show_header=True,
        title=None,
    ):
        """load base paths from file, check existence, print result"""

        printer.title(header)
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
