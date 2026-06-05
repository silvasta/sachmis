import networkx as nx
from pydantic import Field

from .base_dag import BipartiteDAG, Edge, Node


class ConversationNode(Node):
    local_id: int
    name: str = ""


class ConversationEdge(Edge):
    pass


class ConversationDAG(BipartiteDAG):
    nodes: list[ConversationNode] = Field(default_factory=list)
    edges: list[ConversationEdge] = Field(default_factory=list)

    def find_node(self, identifier: str | int) -> ConversationNode | None:
        for node in self.nodes:
            if identifier in (node.id, node.local_id, node.name):
                return node
        return None

    def attach_leaf(self, anchor: str, node: ConversationNode) -> None:
        if any(n.id == node.id for n in self.nodes):
            return
        if not (internal := self.find_node(anchor)):
            return
        edge = ConversationEdge(source=internal.id, target=node.id)
        self.nodes.append(node)
        self.edges.append(edge)

    def copy_subtree(self, root_node_id: str) -> ConversationDAG:
        """Recursively extracts a node and ALL of its descendants."""
        if root_node_id not in self._graph:
            raise ValueError(f"Node '{root_node_id}' not found in the graph.")

        # Gather all descendants recursively (arbitrary depth)
        descendants = nx.descendants(self._graph, root_node_id)
        nodes_to_keep: set[str] = {root_node_id}.union(descendants)

        sub_nodes: list[ConversationNode] = [
            n for n in self.nodes if n.id in nodes_to_keep
        ]
        sub_edges: list[ConversationEdge] = [
            e
            for e in self.edges
            if e.source in nodes_to_keep and e.target in nodes_to_keep
        ]

        return ConversationDAG(nodes=sub_nodes, edges=sub_edges)

    def extract_sprout(self, response_id: str, prompt_name) -> ConversationDAG:
        if not (response := self.find_node(response_id)):
            raise ValueError(f"Invalid { response_id= }")
        prompt = ConversationNode(
            id="xxhd", partition="P", local_id=55, name=prompt_name
        )
        edge = ConversationEdge(source=response.id, target=prompt.id)
        return ConversationDAG(nodes=[prompt], edges=[edge])

    def attach_sprout(
        self, parent_id: str, sprout_dag: ConversationDAG
    ) -> ConversationDAG:
        """
        Connects a sub-DAG to a parent node of this graph.
        Returns a newly validated unified ConversationDAG.
        """
        if not self.find_node(parent_id):
            raise ValueError(f"Parent '{parent_id}' not found in master DAG.")

        # Identify sprout roots (nodes with no parents inside the sprout)
        sprout_roots = [
            n.id
            for n in sprout_dag.nodes
            if sprout_dag.graph.in_degree(n.id) == 0
        ]
        if not sprout_roots:
            raise ValueError("Invalid sprout: No root node detected.")

        # Deep-copy properties to prevent side-effects
        new_nodes: dict[str, ConversationNode] = {n.id: n for n in self.nodes}
        for node in sprout_dag.nodes:
            new_nodes[node.id] = (
                node  # Overwrites/updates existing node config
            )

        new_edges: set[tuple[str, str]] = {
            (e.source, e.target) for e in self.edges
        }
        for edge in sprout_dag.edges:
            new_edges.add((edge.source, edge.target))

        # Dynamically link the master parent to each sprout root
        for root_id in sprout_roots:
            new_edges.add((parent_id, root_id))

        # Re-construct lists and validate everything structural (including bipartite constraints)
        unified_dag = ConversationDAG(
            nodes=list(new_nodes.values()),
            edges=[ConversationEdge(source=s, target=t) for s, t in new_edges],
        )
        return unified_dag
