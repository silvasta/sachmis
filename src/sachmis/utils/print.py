from rich.console import Console
from rich.markdown import Markdown
from rich.theme import Theme
from rich.tree import Tree


class Printer:
    def __init__(self):
        self.custom_theme = Theme(
            {
                "info": "black on white",
                "warning": "yellow",
                "danger": "bold white on red",
                "success": "bold white on green",
                "title": "bold white on cyan",
                "thunder": "bold white on yellow",
                # shortcut lables: can change at any moment!
                "Title": "bold cyan on white",
                # REMOVE: sub-title, after creating and applying concept
                "sub-title": "bold black on white",
                "Info": "bold black on white",
                "bw": "black on white",
                "wb": "white on black",
                "write": "bold white on green",
            }
        )
        self.console = Console(theme=self.custom_theme)

    def print(self, *args, **kwargs) -> None:
        """Regular rich console print"""
        self.console.print(*args, **kwargs)

    def title(self, text, style="title") -> None:
        """Centred H1 title"""
        self.console.print(
            Markdown(f"# {text}"),
            justify="center",
            style=style,
        )

    def thunder(self, text, style="thunder"):
        self.title(text, style=style)

    def success(self, text) -> None:
        """Centred H2 Success message"""
        self.console.print(
            Markdown(f"## {text}"),
            justify="center",
            style="success",
        )

    def fail(self, text) -> None:
        """Centred H2 Failure message"""
        self.console.print(
            Markdown(f"## {text}"),
            justify="center",
            style="danger",
        )

    def md(self, content, style="info", H: int = 0) -> None:
        """Generic Markdown printer"""
        if 6 < H < 0:
            self.fail(f"{H=} but Markdown Header level is from H1 to H6")
        else:
            prefix: str = "#" * H + " " if H > 0 else ""
            self.console.print(
                Markdown(f"{prefix}{content}"),
                style=style,
            )

    def forest(self, forest_data) -> None:
        """Visualizes a Forest model as a nested Rich Tree"""
        # Create the visual root (the Forest itself)
        root_label = (
            f"[bold green]Forest:[/bold green] {forest_data.tree_file_path.name}"
        )
        visual_tree = Tree(root_label)

        # 1. Group trees by their ancestor for quick lookup
        from collections import defaultdict

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


printer = Printer()
