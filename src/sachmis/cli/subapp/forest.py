import typer
from sstcore.cli import attach_callback, logger_catch

from ...config import SachmisConfig, get_config
from ...data.arboreal import ArborealTracker, Forest, Tree
from ...utils.print import printer


def main() -> None:
    app()


app = typer.Typer(
    name="forest",
    help="Forest - Home of every Tree",
    no_args_is_help=True,
)
attach_callback(app)


@app.command()
@logger_catch
def prune():
    """Delete Tracker with missing Trees in Forest"""
    config: SachmisConfig = get_config()

    active: str = "[bold]Active:[/]"
    printer.title(f"{active} {config.paths.forest_file}", style="warning")

    with Forest.edit_mode(config.paths.forest_file) as forest:
        trees: list[ArborealTracker] = forest.trees
        printer.path_exists_table([tree.path for tree in trees])

        deleted: list[ArborealTracker] = (
            forest.prune_tracker_with_missing_paths()
        )

    to_print: list[str] = []
    for tree in deleted:
        name: str = tree.path.stem
        to_print.append(f"[bold black on white]{name}[/] - {tree.path}")

    printer.lines_with_len(
        name="Deleted Trees",
        lines=to_print,
    )


@app.command()
@logger_catch
def stat():
    """Show statistics of active Forest"""
    # LATER: generic for Arbo
    config: SachmisConfig = get_config()

    active: str = "[bold]Active:[/]"
    printer.title(f"{active} {config.paths.forest_file}", style="warning")

    forest: Forest = Forest.read_mode(config.paths.forest_file)
    trees: list[ArborealTracker] = forest.trees

    to_print: list[str] = []
    for tree in trees:
        name: str = tree.path.stem
        to_print.append(f"[bold black on white]{name}[/] - {tree.path}")

    printer.lines_with_len(
        name="Trees",
        lines=to_print,
    )
    printer.path_exists_table([tree.path for tree in trees])

    for tree in trees:
        if not tree.path.exists():
            printer(f"Missing Tree: {tree.path.name}")
            continue
        loaded_tree: Tree = Tree.read_mode(tree.path)
        printer(tree.path.name, loaded_tree.stat)


if __name__ == "__main__":
    main()
