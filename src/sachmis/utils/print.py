from collections import defaultdict

from rich.tree import Tree
from silvasta.utils.print import Printer

custom_theme: dict[str, str] = {
    # TODO: modify/delete after adapting code
    "write": "bold white on green",
}


class SachmisPrinter(Printer):
    def forest(self, forest_data) -> None:
        """Visualizes a Forest model as a nested Rich Tree"""

        # LATER: adapt this to new setup

        # Create the visual root (the Forest itself)
        root_label = (
            f"[bold green]Forest:[/bold green] {forest_data.tree_file_path.name}"
        )
        visual_tree = Tree(root_label)

        # 1. Group trees by their ancestor for quick lookup
        by_ancestor = defaultdict(list)
        for tree_id, tree_obj in forest_data.trees.items():
            by_ancestor[tree_obj.ancestor].append(tree_obj)

        # 2. Recursive function to add children
        def add_children(parent_visual, ancestor_id: str):
            children = by_ancestor.get(ancestor_id, [])
            for child in children:
                # Create a nice label for each node
                node_label = f"[cyan]ID:[/cyan] {child.tree_stem} [dim]({child.created_at})[/dim]"
                node_visual = parent_visual.add(node_label)
                # Recursively add this child's descendants
                add_children(node_visual, child.id)

        # 3. Start recursion from the actual roots (empty ancestor string)
        add_children(visual_tree, "")

        self.console.print(visual_tree)


printer = SachmisPrinter(custom_theme)
