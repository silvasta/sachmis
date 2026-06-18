import random
from collections import defaultdict
from typing import Literal

import networkx as nx
from pydantic import BaseModel, Field, PrivateAttr, model_validator

# NEXT: load to prompt, send


class Node(BaseModel):
    # AI: if the label can be some property here, then it is easy
    uuid: str
    partition: Literal["P", "R"]
    metadata: dict = Field(default_factory=dict)  # LATER: check again remove


class Edge(BaseModel):
    # AI: unsure how nx reads from here for draw()
    source: str
    target: str


class BipartiteDAG(BaseModel):
    """Validated Bipartite DAG (all edges P → R)."""

    nodes: list[Node]
    edges: list[Edge] = Field(default_factory=list)

    _node_map: dict[str, Literal["P", "R"]] = PrivateAttr(default_factory=dict)
    _graph: nx.DiGraph = PrivateAttr(default_factory=nx.DiGraph)

    @model_validator(mode="after")
    def validate_bipartite_dag(self) -> BipartiteDAG:
        self._node_map: dict[str, Literal["P", "R"]] = {
            node.uuid: node.partition for node in self.nodes
        }
        if len(self._node_map) != len(self.nodes):
            raise ValueError("Node IDs must be unique")

        self._graph = nx.DiGraph()
        for node in self.nodes:
            self._graph.add_node(
                node_for_adding=node.uuid, partition=node.partition
            )

        for edge in self.edges:
            if (
                edge.source not in self._node_map
                or edge.target not in self._node_map
            ):
                raise ValueError(f"Edge references unknown node: {edge}")
            src_part: Literal["P", "R"] = self._node_map[edge.source]
            tgt_part: Literal["P", "R"] = self._node_map[edge.target]

            if src_part == tgt_part:
                raise ValueError(f"Intra-partition edge not allowed: {edge}")

            self._graph.add_edge(edge.source, edge.target)

        if not nx.is_directed_acyclic_graph(self._graph):
            raise ValueError("Graph contains cycles - not a DAG")

        return self

    @property
    def graph(self) -> nx.DiGraph:
        return self._graph

    def topological_sort(self) -> list[str]:
        return list(nx.topological_sort(self._graph))

    def get_partition(self, part: Literal["P", "R"]) -> set[str]:
        return {nid for nid, p in self._node_map.items() if p == part}

    def _compute_levels(self) -> dict[str, int]:
        """Layer of each node = length of longest path from any source."""
        levels: dict[str, int] = {}
        for node in nx.topological_sort(self.graph):
            if self.graph.in_degree(node) == 0:
                levels[node] = 0
            else:
                levels[node] = (
                    max(levels[pred] for pred in self.graph.predecessors(node))
                    + 1
                )
        return levels

    def draw(  # AI: this I want to use for plots
        self,
        figsize: tuple[int, int] | None = None,
        use_graphviz: bool = False,
    ):
        """Standardized visualizer using PyGraphviz layout or custom layers."""
        import matplotlib.pyplot as plt

        pos = None
        if use_graphviz:
            try:
                pos = nx.nx_agraph.graphviz_layout(self._graph, prog="dot")
                title = "Bipartite DAG (Graphviz dot Layout)"
            except Exception:
                print(
                    "Graphviz (pygraphviz) not available. Falling back to custom layout."
                )

        if pos is None:
            levels = self._compute_levels()
            layer_nodes = defaultdict(list)
            for node, lvl in levels.items():
                layer_nodes[lvl].append(node)

            pos = {}
            for lvl, nodes in sorted(layer_nodes.items()):
                sorted_nodes = sorted(nodes)
                n = len(sorted_nodes)
                for i, node in enumerate(sorted_nodes):
                    y = i - (n - 1) / 2.0
                    pos[node] = (lvl * 2.0, y)

            max_lvl = max(levels.values()) if levels else 0
            title = f"Layered Layout ({max_lvl + 1} layers)"

        if figsize is None:
            max_x = max(x for x, _ in pos.values()) if pos else 5
            figsize = (max(10, int(max_x * 1.4)), 8)

        plt.figure(figsize=figsize)
        colors = [
            "skyblue" if self._node_map.get(n) == "P" else "lightgreen"
            for n in self._graph.nodes()
        ]
        nx.draw(
            self._graph,
            pos,
            with_labels=True,
            node_color=colors,
            node_size=1500,
            arrows=True,
            arrowsize=20,
            font_size=9,
            font_weight="bold",
        )
        plt.title(title, fontsize=12, fontweight="bold")
        plt.axis("off")
        plt.tight_layout()
        plt.show()

    @classmethod
    def generate_layered(
        cls,
        num_layers: int = 10,
        min_nodes_per_layer: int = 1,
        max_nodes_per_layer: int = 5,
        seed: int = 42,
    ) -> BipartiteDAG:
        """Create a nice deep DAG with one root and alternating partitions."""
        random.seed(seed)
        nodes: list[Node] = []
        edges: list[Edge] = []

        # Root
        nodes.append(Node(uuid="Root", partition="P"))
        prev_layer = ["Root"]

        for layer_idx in range(1, num_layers + 1):
            partition = "R" if layer_idx % 2 == 1 else "P"
            n_nodes = random.randint(min_nodes_per_layer, max_nodes_per_layer)
            current_layer = []

            for i in range(n_nodes):
                node_id = f"{partition}{layer_idx}_{i + 1}"
                nodes.append(Node(uuid=node_id, partition=partition))
                current_layer.append(node_id)

            # Each node in previous layer connects to 1–3 random targets
            for src in prev_layer:
                k = min(len(current_layer), random.randint(1, 3))
                targets = random.sample(current_layer, k)
                for tgt in targets:
                    edges.append(Edge(source=src, target=tgt))

            prev_layer = current_layer

        dag = cls(nodes=nodes, edges=edges)
        print(
            f"Generated {num_layers + 1}-layer DAG with {len(nodes)} nodes, {len(edges)} edges"
        )
        return dag
