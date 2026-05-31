import networkx as nx
from pydantic import Field, PrivateAttr, model_validator

from sachmis.exceptions import ArborealRegistryMissingError

from .base_dag import BipartiteDAG, Edge, Node


class ConversationNode(Node):
    local_id: int
    name: str = ""

    @property
    def uuid(self) -> str:
        """Helper property to match your internal naming convention."""
        return self.id


class ConversationEdge(Edge):
    @property
    def source_uuid(self) -> str:
        return self.source

    @property
    def target_uuid(self) -> str:
        return self.target


class ConversationDAG(BipartiteDAG):
    nodes: list[ConversationNode] = Field(default_factory=list)
    edges: list[ConversationEdge] = Field(default_factory=list)

    # Private attribute to hold the actual NetworkX graph for traversal logic
    _nx_graph: nx.DiGraph = PrivateAttr(default_factory=nx.DiGraph)

    @model_validator(mode="after")
    def sync_and_validate_conversation_dag(self) -> ConversationDAG:
        self._sync_to_nx()
        return self

    def _sync_to_nx(self):
        """Populates the hidden NetworkX graph using Pydantic data."""
        self._nx_graph.clear()
        for node in self.nodes:
            self._nx_graph.add_node(node.uuid, **node.model_dump())
        for edge in self.edges:
            self._nx_graph.add_edge(edge.source_uuid, edge.target_uuid)

    def find_node(self, identifier: str | int) -> ConversationNode | None:
        """Find a node by uuid, local_id, or name."""
        for node in self.nodes:
            if identifier in (node.uuid, node.local_id, node.name):
                return node
        return None

    def copy_subtree(self, current_node_uuid: str) -> ConversationDAG:
        """Extracts a node and its successors into a new lightweight DAG."""

        if current_node_uuid not in self._nx_graph:
            raise ValueError(f"Node {current_node_uuid} not found in graph.")

        successors = list(self._nx_graph.successors(current_node_uuid))
        nodes_to_keep = [current_node_uuid] + successors

        sub_nodes = [n for n in self.nodes if n.uuid in nodes_to_keep]
        sub_edges = [
            e
            for e in self.edges
            if e.source_uuid in nodes_to_keep
            and e.target_uuid in nodes_to_keep
        ]

        return ConversationDAG(nodes=sub_nodes, edges=sub_edges)

    def attach_sprout(
        self, parent_uuid: str, sprout_dag: ConversationDAG
    ) -> None:
        """Merges a returning Sprout DAG back into this master DAG."""
        if not self.find_node(parent_uuid):
            raise ValueError(
                f"Parent UUID {parent_uuid} not found in master DAG."
            )

        # Identify the root of the incoming sprout (node with no internal parents)
        sprout_root_uuid = None
        for node in sprout_dag.nodes:
            if sprout_dag._nx_graph.in_degree(node.id) == 0:
                sprout_root_uuid = node.id
                break

        if not sprout_root_uuid:
            raise ArborealRegistryMissingError(
                parent="Sprout", child="Sprout", missing_id=parent_uuid
            )

        # Deduplicate and append incoming nodes
        existing_uuids = {n.id for n in self.nodes}
        for node in sprout_dag.nodes:
            if node.id not in existing_uuids:
                self.nodes.append(node)

        # Append edges
        existing_edges = {(e.source, e.target) for e in self.edges}
        for edge in sprout_dag.edges:
            if (edge.source, edge.target) not in existing_edges:
                self.edges.append(edge)

        # Connect the master graph to the sprout's root node if it doesn't already link
        if (parent_uuid, sprout_root_uuid) not in existing_edges:
            self.edges.append(
                ConversationEdge(source=parent_uuid, target=sprout_root_uuid)
            )

        # Trigger Pydantic model rebuild/revalidation to refresh maps & networks
        self.model_validate(self.model_dump())
