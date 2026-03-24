from pathlib import Path

from silvasta.cli import monitor
from silvasta.cli.setup import logger_catch

import sachmis.core.capstone as cap
from sachmis.utils.print import printer


@logger_catch
def data():
    """Open DataManger in Context: with DataManger() as data..."""
    printer.md("Maybe something to show could be useful")
    cap.test_data_in_context()


@logger_catch
def print_file(path: Path):
    """Print prompt, answer or any Markdown file in Rich style"""
    printer.md(path.read_text())


@logger_catch
def launch_monitor(file: Path | None = None):
    """Launch Log Console Monitor: watch new log file entries"""
    monitor(log_path=file)
