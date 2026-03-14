from typing import Type

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static
from ..utils.logging_config import setup_logging

from loguru import logger


def main():
    setup_logging(log_to_stderr=False)
    # Use context manager so we can execute code AFTER a potential crash
    with logger.catch():
        logger.info("Launch Combined TUI")
        tui = ProjectApp()
        tui.run()

    # If we are here, and an error happened, it's already in the log.
    # We could print a hint here if we detected an error state.


class StartScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Pop screen"),
    ]

    def compose(self) -> ComposeResult:
        yield Static(" Screen ", id="title")
        yield Static("Your advertisement could be here")
        yield Static("Press any key to continue [blink]_[/]", id="any-key")


class ProjectApp(App):
    """project description"""

    CSS_PATH = "sakhmat.tcss"
    BINDINGS: list[Binding] = [
        Binding("ctrl+z", "suspend_process"),
    ]
    SCREENS: dict[str, Type[Screen]] = {
        # mount screens that should be installed here
        "start_screen": StartScreen,
    }

    def on_mount(self) -> None:
        """Run on app start."""
        self.title: str = "sakhmat"
        self.sub_title: str = "hello"
        # Push the start screen
        self.push_screen("start_screen")
        logger.info("TUI Mounted successfully")
