import uuid

import networkx as nx
from pydantic import Field

from .base_dag import BipartiteDAG, Edge, Node


class ConversationNode(Node):
    sprout_id: int
    topic: str = ""
    tree_id: int


class ConversationEdge(Edge):
    pass


class ConversationDAG(BipartiteDAG):
    nodes: list[ConversationNode] = Field(default_factory=list)
    edges: list[ConversationEdge] = Field(default_factory=list)

    def find_node(self, target_uuid: str) -> ConversationNode | None:
        for node in self.nodes:
            if target_uuid == node.uuid:
                return node
        return None

    def find_sprout_group(self, sprout_id: int) -> list[ConversationNode]:
        return [
            node  #
            for node in self.nodes
            if sprout_id == node.sprout_id
        ]

    def attach_leaf(self, internal_uuid: str, new_node: ConversationNode):
        if any(node.uuid == new_node.uuid for node in self.nodes):
            return None
        if not (internal := self.find_node(internal_uuid)):
            return None
        edge = ConversationEdge(source=internal.uuid, target=new_node.uuid)
        self.nodes.append(new_node)
        self.edges.append(edge)

    def copy_subtree(self, root_node_id: str) -> ConversationDAG:
        """Recursively extracts a node and ALL of its descendants."""
        if root_node_id not in self._graph:
            raise ValueError(f"Node '{root_node_id}' not found in the graph.")

        # Gather all descendants recursively (arbitrary depth)
        descendants = nx.descendants(self._graph, root_node_id)
        nodes_to_keep: set[str] = {root_node_id}.union(descendants)

        sub_nodes: list[ConversationNode] = [
            node for node in self.nodes if node.uuid in nodes_to_keep
        ]
        sub_edges: list[ConversationEdge] = [
            edge
            for edge in self.edges
            if edge.source in nodes_to_keep and edge.target in nodes_to_keep
        ]

        return ConversationDAG(nodes=sub_nodes, edges=sub_edges)

    def extract_sprout(
        self, response_id: str, sprout_id: int, topic: str, tree_id: int
    ) -> ConversationDAG:
        if not (response := self.find_node(response_id)):
            raise ValueError(f"Invalid { response_id= }")
        prompt = ConversationNode(
            uuid=str(uuid.uuid4()),
            partition="P",
            sprout_id=sprout_id,
            topic=topic,
            tree_id=tree_id,
        )
        edge = ConversationEdge(source=response.uuid, target=prompt.uuid)
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
            node.uuid
            for node in sprout_dag.nodes
            if sprout_dag.graph.in_degree(node.uuid) == 0
        ]
        if not sprout_roots:
            raise ValueError("Invalid sprout: No root node detected.")

        # Deep-copy properties to prevent side-effects
        new_nodes: dict[str, ConversationNode] = {
            node.uuid: node for node in self.nodes
        }
        for node in sprout_dag.nodes:
            # Overwrites/updates existing node config
            new_nodes[node.uuid] = node

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
