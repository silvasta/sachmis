from itertools import cycle

from loguru import logger
from rich.table import Table
from sstcore.exceptions import NotImplementedDispatchError
from sstcore.utils import Printer


class SachmisPrinter(Printer):
    project_debugs: bool = False

    def debug(self, target: str, *lines, simple=True, stop=False):
        """Print debug stuff with unified interface and global toggle"""

        if not self.project_debugs:
            return

        self._debug_title(text=target)

        _print = self(lines) if simple else self._debug_line_by_line(*lines)

        if stop:
            input(f"ENTER: {target}")

    def _debug_line_by_line(self, *lines):
        sub_color: str = "navajo_white1"
        for line in lines:
            try:
                self._debug_title(line, frame=sub_color)
            except NotImplementedDispatchError as error:
                logger.warning(f"Printer failed: {error=}")
                self._debug_title(str(line), frame=sub_color)
            self(line)

    def _debug_title(self, text: str, frame: str = ""):
        top_color: str = "orange_red1"
        title: str = self.colors.white(f"{self.colorful} debug print")
        self.title(text, title=title, frame=frame or top_color)

    @property
    def colorful(self):
        return self.colors.s(self.__class__.__name__)

    def conversation_transition_result(
        self, prompt: str, response: str, result: bool, from_prompt: bool
    ):
        # MOVE: maybe to cli.sketch
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
        # REMOVE: maybe already replaced in cli.sketch

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
