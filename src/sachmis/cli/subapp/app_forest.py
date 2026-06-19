from sstcore.cli import SafeTyper
from sstcore.utils.paint import ColorBox

from ...config import config
from ...data.arboreal import ArborealTracker, Forest, Tree
from ...utils.print import printer


def main() -> None:
    app()


app = SafeTyper(
    name="forest",
    help="Forest - Home of every Tree",
)


@app.command()
def trees(id: int = 0):  # TASK:  generic for Arbo
    """Show statistics of active Forest"""

    printer.title(f"Loading {config().paths.forest_file}", style="warning")

    forest: Forest = Forest.read_mode(config().paths.forest_file)
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
def stat():  # TASK:  generic for Arbo
    """Show statistics of active Forest"""
    c: ColorBox = ColorBox.with_mode("bold")

    printer.title(f"Loading {config().paths.forest_file}", style="warning")

    forest: Forest = Forest.read_mode(config().paths.forest_file)
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
