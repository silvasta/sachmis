from typing import Literal, Self

import networkx as nx
from loguru import logger
from pydantic import Field

from sachmis.config.models import ModelFamily

from ...utils import printer
from .base import SproutData
from .base_dag import BipartiteDAG, Edge, Node
from .prompt import Prompt
from .response import Response


class SproutNode(Node):
    """Base Node for Prompt and Response"""

    @property
    def sprout_id(self) -> int:
        return self._data.sprout_id

    @property
    def _data(self) -> SproutData:
        raise NotImplementedError


class PromptNode(SproutNode):
    partition: Literal["P"] = "P"
    prompt: Prompt

    @property
    def _data(self) -> Prompt:
        return self.prompt

    @classmethod
    def from_prompt(cls, prompt: Prompt) -> Self:
        return cls(uuid=prompt.unique_id, prompt=prompt)


class ResponseNode(SproutNode):
    partition: Literal["R"] = "R"
    response: Response

    @property
    def _data(self) -> Response:
        return self.response

    @classmethod
    def from_response(cls, response: Response) -> Self:
        return cls(uuid=response.unique_id, response=response)


class SproutEdge(Edge):
    """Intended to apply Status or Weight to SproutEdge"""


class SproutDAG(BipartiteDAG):
    nodes: list[SproutNode] = Field(default_factory=list)
    edges: list[SproutEdge] = Field(default_factory=list)

    @classmethod
    def init(cls, prompt: Prompt) -> Self:
        return cls(nodes=[PromptNode.from_prompt(prompt)])

    @property
    def prompts(self) -> list[Prompt]:
        return [node for node in self.nodes if isinstance(node, Prompt)]

    @property
    def responses(self) -> list[Response]:
        return [node for node in self.nodes if isinstance(node, Response)]

    @property
    def n_prompts(self) -> int:
        return len(self.prompts)

    @property
    def n_responses(self) -> int:
        return len(self.responses)

    # IMPORTANT: new DAG functions
    # predecessor, ancestor, all predecessor,...
    # - maybe SproutSproutEdge
    # - all "living" or "dead" ancestor Model conversations

    def find_node(self, target_uuid: str) -> SproutNode | None:
        for node in self.nodes:
            if target_uuid == node.uuid:
                return node
        return None

    def find_sprout_group(self, sprout_id: int) -> list[SproutNode]:
        return [
            node  #
            for node in self.nodes
            if sprout_id == node.sprout_id
        ]

    def find_previous_model_response_from_sprout(
        self, model: ModelFamily, sprout_id: int
    ) -> ResponseNode | None:

        sprout_group: list[SproutNode] = self.find_sprout_group(sprout_id)
        logger.debug(f"found {model=}: {sprout_group=}")

        for node in sprout_group:  # TEST:
            if node.partition == "P":
                logger.debug(f"ignoring prompt: {node=}")
            else:
                assert isinstance(node, ResponseNode)
                response: Response = node.response
                printer(("Found: ", response))  # REMOVE:
                if response.model == model:
                    logger.success(f"Found: {node=}")
                    return node

    def attach_leaf(self, target_uuid: str, new_node: SproutNode):
        if any(node.uuid == new_node.uuid for node in self.nodes):
            return None
        if not (internal := self.find_node(target_uuid)):
            return None
        edge = SproutEdge(source=internal.uuid, target=new_node.uuid)
        self.nodes.append(new_node)
        self.edges.append(edge)

    def copy_subtree(self, root_node_id: str) -> SproutDAG:
        """Recursively extracts a node and ALL of its descendants."""

        printer(self._graph)
        self.draw()
        if root_node_id not in self._graph:
            raise ValueError(f"Node '{root_node_id}' not found in the graph.")

        # Gather all descendants recursively (arbitrary depth)
        descendants = nx.descendants(self._graph, root_node_id)
        nodes_to_keep: set[str] = {root_node_id}.union(descendants)

        sub_nodes: list[SproutNode] = [
            node for node in self.nodes if node.uuid in nodes_to_keep
        ]
        sub_edges: list[SproutEdge] = [
            edge
            for edge in self.edges
            if edge.source in nodes_to_keep and edge.target in nodes_to_keep
        ]

        sub_dag = SproutDAG(nodes=sub_nodes, edges=sub_edges)
        printer.special("Sub DAG")
        printer(sub_dag)  # REMOVE:

        return sub_dag

    def attach_sprout(
        self, parent_id: str, sprout_dag: SproutDAG
    ) -> SproutDAG:
        """
        Connects a sub-DAG to a parent node of this graph.
        Returns a newly validated unified SproutDAG.
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
        new_nodes: dict[str, SproutNode] = {
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
        return SproutDAG(
            nodes=list(new_nodes.values()),
            edges=[SproutEdge(source=s, target=t) for s, t in new_edges],
        )
