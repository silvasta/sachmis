from pathlib import Path

from silvasta.cli import monitor
from silvasta.cli.setup import logger_catch

import sachmis.core.capstone as cap
from sachmis.cli import args
from sachmis.config import SachmisConfig, get_config
from sachmis.data import DataManager
from sachmis.utils.print import printer

config: SachmisConfig = get_config()


@logger_catch
def init(name: args.Name = config.names.base_dir):
    """Create new Base with Forest and Local Data Structure"""
    DataManager.create_new_base(name)


@logger_catch
def launch_monitor(file: args.File = None):  # NOTE: CLI hint not amazing...
    """Launch Log Console Monitor: watch new log file entries"""
    monitor(log_path=file)


@logger_catch
def print_file(path: Path):
    """Print Prompt, Response or any Markdown file in Rich style"""
    printer.md(path.read_text())


@logger_catch
def data():
    """Open DataManger in Context: with DataManger() as data..."""
    printer.md("Maybe something to show could be useful")
    cap.test_data_in_context()
