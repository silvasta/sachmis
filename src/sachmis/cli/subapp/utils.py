from pathlib import Path

import typer
from sstcore.cli import attach_callback, logger_catch, monitor, sargs, scanner

from ...data import DataManager
from ...utils.print import printer
from .. import args


def main() -> None:
    app()


app = typer.Typer(
    name="utils",
    help="Show statistics, configurations and more",
    no_args_is_help=True,
)
attach_callback(app)


@app.command("monitor")
@logger_catch  # MOVE: sstcore.collection?
def launch_monitor(file: sargs.File = None):  # NOTE: CLI hint not amazing...
    """Launch Log Console Monitor: watch new log file entries"""
    monitor(log_path=file)


@app.command("scanner")
@logger_catch  # MOVE: sstcore.collection?
def folder_scanner(
    scan_root: sargs.Root = None,
    output_file: args.OutputFile = None,
    print_debug_logs=False,  # LATER: Generalize this
):
    """Launch Folder Scanner with TreeSelector: write combined file"""
    scanner(scan_root, output_file, print_debug_logs)


@app.command("print")
@logger_catch  # MOVE: sstcore.collection?
def print_file(path: Path):
    """Print Prompt, Response or any Markdown file in Rich style"""
    printer.title(path.name)
    match path.suffix:
        case ".json":
            printer(path.read_text())
        case ".md":
            printer.md(path.read_text())
        case _:
            # LATER: define other file types?
            # - match as function of sstcore.Printer!
            printer.md(path.read_text())


@app.command()
@logger_catch
def data(biome: bool = False, forest: bool = False, camp: bool = False):
    """Open DataManger in Context: with DataManger() as data..."""

    with DataManager(biome, forest, camp) as data:
        printer(vars(data))


if __name__ == "__main__":
    main()
