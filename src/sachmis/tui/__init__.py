from loguru import logger
from silvasta.utils import setup_logging
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static

# LATER: ...


def main():
    setup_logging(quiet=False)
    with logger.catch():
        logger.info("Launch Combined TUI")
        tui = ProjectApp()
        tui.run()


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

    CSS_PATH = "sachmis.tcss"
    BINDINGS: list[Binding] = [
        Binding("ctrl+z", "suspend_process"),
    ]
    SCREENS: dict[str, type[Screen]] = {
        # mount screens that should be installed here
        "start_screen": StartScreen,
    }

    def on_mount(self) -> None:
        """Run on app start."""
        self.title: str = "sachmis"
        self.sub_title: str = "hello"
        # Push the start screen
        self.push_screen("start_screen")
        logger.info("TUI Mounted successfully")
