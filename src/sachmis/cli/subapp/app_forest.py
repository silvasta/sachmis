from sachmis.config import SachmisConfig
from typer import Context
from sstcore import SafeTyper, System, printer
from sstcore.utils.color import ColorBox

from ...data.arboreal import ArborealTracker, Forest, Tree


def main() -> None:
    app()


app = SafeTyper(
    name="forest",
    help="Forest - Home of every Tree",
)


@app.command()
def trees(
    ctx: Context,
    id: int = 0,
):  # TASK:  generic for Arbo
    """Show statistics of active Forest"""

    config: SachmisConfig = ctx.obj["config"]

    # TODO: emit?
    _sst: System = ctx.obj["config"]
    printer.title(f"Loading {config.paths.forest_file}", style="warning")

    forest: Forest = Forest.read_mode(config.paths.forest_file)
    trees: list[ArborealTracker] = forest.trees

    for t in trees:
        if id and t.local_id != id:
            continue
        tree: Tree = Tree.read_mode(t.local_path)
        printer.title(tree.colorful)
        # LATER: sample SimpleTree for: printer.tree_graph()
        printer(tree)
        tree.draw()


@app.command()
def stat(ctx: Context):
    """Show statistics of active Forest"""
    config: SachmisConfig = ctx.obj["config"]
    c: ColorBox = ColorBox.bold()

    printer.title(f"Loading {config.paths.forest_file}", style="warning")

    forest: Forest = Forest.read_mode(config.paths.forest_file)
    trees: list[ArborealTracker] = forest.trees

    printer.path_exists_table([tree.path for tree in trees])

    g3 = "spring_green3"
    g4 = "spring_green4"
    start = "TreeStatistic"
    for tree in trees:
        loaded_tree: Tree = Tree.read_mode(tree.path)
        printer.header(f"{c(start, g3)} - {tree.stem}", frame=g3)
        printer.header(f"{c(start, g3)} - {tree.stem}", frame=g4)
        printer.header(f"{c(start, g4)} - {tree.stem}", frame=g3)
        printer.header(f"{c(start, g4)} - {tree.stem}", frame=g4)
        printer(loaded_tree)


if __name__ == "__main__":
    main()
