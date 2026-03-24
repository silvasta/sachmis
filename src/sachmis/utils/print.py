from collections import defaultdict
from pathlib import Path

from rich.markdown import Markdown
from rich.table import Table
from rich.tree import Tree
from silvasta.utils.print import Printer

custom_theme: dict[str, str] = {
    # TODO: modify/delete after adapting code
    "write": "bold white on green",
    "aware": "bold white on red",
}


class SachmisPrinter(Printer):
    def forest(self, forest_data) -> None:
        """Visualizes a Forest model as a nested Rich Tree"""

        # LATER: adapt this to new setup

        # IMPORTANT: style counter!
        # - count which default/not default used and improve

        # Create the visual root (the Forest itself)
        root_label = f"[bold green]Forest:[/bold green] {forest_data.tree_file_path.name}"
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

        self(visual_tree)

    def yellow(self, text: str, *args, **kwargs):
        printer(text, *args, style="yellow", **kwargs)

    def aware(self, text: str, *args, **kwargs):
        printer.panel(text, *args, style="aware", title="Check!", **kwargs)

    def path_exists_table(self, paths: list[Path], title=None, header="Path"):
        """load base paths from file, check existance, print result"""

        # INFO: candidate for silvasta.printer

        table = Table(title=title)
        table.add_column("Status", justify="center")
        table.add_column(header, style="cyan")

        for path in paths:
            status: str = "✅" if path.exists() else ""
            table.add_row(status, str(path))

        self(table)

    def preview(self, title: str, lines: list):
        """Print header followed by items per line in panel"""
        printer.title(title)
        self.panel(text="\n".join(lines), title=title)


printer = SachmisPrinter(custom_theme)

if __name__ == "__main__":
    title = "# Models"
    printer.console.print(Markdown(title))
    models = [
        # "sss",
        # "sss",
        # "sss",
        # "sss",
        # "sss",
    ]
    printer.panel(text="\n".join(models), title=title)
    printer.aware("Last check before deployment")
