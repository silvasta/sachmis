from pathlib import Path

from rich.markdown import Markdown
from rich.table import Table
from silvasta.utils.print import Printer

custom_theme: dict[str, str] = {
    # "write": "bold white on green",
    # LATER: now everything gone...
    # store for future use?
}

# LATER: probably still needed, specific prompt/llm prints?


class SachmisPrinter(Printer):
    def yellow(self, text: str, *args, **kwargs):
        # TODO: check
        printer(text, *args, style="yellow", **kwargs)

    def path_exists_table(self, paths: list[Path], title=None, header="Path"):
        """load base paths from file, check existance, print result"""

        # NEXT: candidate for silvasta.printer

        table = Table(title=title)
        table.add_column("Status", justify="center")
        table.add_column(header, style="cyan")

        for path in paths:
            status: str = "✅" if path.exists() else ""
            table.add_row(status, str(path))

        self(table)


printer = SachmisPrinter(custom_theme)

if __name__ == "__main__":
    title = "# Models"
    printer.console.print(Markdown(title))
    models = [
        # "sss",
        # "sss",
        # "sss",
        # "sss",
        # "sss",
    ]
    printer.panel(text="\n".join(models), title=title)
    printer.danger("Last check before deployment")
