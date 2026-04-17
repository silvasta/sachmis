import typer
from silvasta.tui.picker import TreeSelectorApp  # Import the app we just made
from silvasta.utils.print import printer  # Your custom rich printer
from silvasta.utils.simple_tree import SimpleTreeNode

app = typer.Typer()

tree1 = SimpleTreeNode("tree1", next=[])
tree2 = SimpleTreeNode("tree2", next=[])
tree3 = SimpleTreeNode("tree3", next=[])
tree4 = SimpleTreeNode("tree4", next=[])
tree5 = SimpleTreeNode("tree5", next=[])
tree6 = SimpleTreeNode("tree6", next=[])
tree7 = SimpleTreeNode("tree7", next=[])
tree8 = SimpleTreeNode("tree8", next=[])
tree9 = SimpleTreeNode("tree9", next=[])
tree10 = SimpleTreeNode("tree10", next=[])
tree11 = SimpleTreeNode("tree11", next=[])
tree12 = SimpleTreeNode("tree12", next=[])

forest1 = SimpleTreeNode("forest1", next=[tree1, tree2])
forest2 = SimpleTreeNode("forest2", next=[tree3, tree4, tree5])
forest3 = SimpleTreeNode("forest3", next=[tree6, tree7, tree8])
forest4 = SimpleTreeNode("forest4", next=[tree9, tree10, tree11])
forest5 = SimpleTreeNode("forest5", next=[tree12])

biome = SimpleTreeNode(
    "biome",
    next=[
        forest1,
        forest2,
        forest3,
        forest4,
        forest5,
    ],
)


@app.command()
def process_tree(
    target_node: str = typer.Argument(
        None, help="The exact ID/name of the node to process"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Use TUI picker"
    ),
):
    """Process a specific node in the forest."""

    # 1. Load your dummy data (in reality, from your DataManager)
    # leaf1 = SimpleTreeNode("tree1")
    # leaf2 = SimpleTreeNode("tree2")
    # forest = SimpleTreeNode("forest1", next=[leaf1, leaf2])
    # root = SimpleTreeNode("biome", next=[forest])

    # 2. Handle Interactive Mode
    if interactive:
        # Launch TUI and wait for return value
        tui = TreeSelectorApp(tree_data=biome)
        selected_node = tui.run()

        if not selected_node:
            printer.warn("Action cancelled by user.")
            raise typer.Exit()

        # Reassign target_node so the rest of the script works exactly the same
        target_node = selected_node

    # 3. Handle Missing Argument in standard CLI mode
    elif target_node is None:
        printer.danger(
            "You must provide a target_node or use the --interactive flag!"
        )
        raise typer.Exit(code=1)

    # 4. Resume normal CLI logic
    printer.success(f"Successfully selected node: {target_node}")
    # cap.process_data(target_node) ...


if __name__ == "__main__":
    app()
