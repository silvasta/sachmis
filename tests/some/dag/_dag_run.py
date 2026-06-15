import uuid
from pathlib import Path

from loguru import logger

from sachmis.data.arboreal import Tree
from sachmis.data.conversation import (
    ConversationEdge,
    ConversationNode,
    Prompt,
    Response,
)


def generate_mock_prompt(local_id: int, content: str) -> Prompt:
    """Helper to bypass file/config loads for isolated testing."""
    return Prompt(
        local_id=local_id,
        topic=Prompt.extract_topic(content),
        _content=content,
        partition="P",
    )


def generate_mock_response(
    local_id: int, prompt_uuid: str, content: str
) -> Response:
    return Response(
        local_id=local_id,
        topic="mock-response",
        model="mock-gpt-4o",
        remote_id=f"req_{uuid.uuid4().hex[:8]}",
        _content=content,
        usage={"total_tokens": 42},
        full_response=Path(f"/tmp/mock_resp_{local_id}.json"),
        partition="R",
    )


def run_mock_workflow():
    logger.info("Initializing Mock Tree Environment...")

    # 1. Setup Mock Tree
    tree_path = Path("/tmp/mock_tree.json")
    # Using a fake tracker for the sake of bypassing Arboreal Disk checks
    tree = Tree.create_with_tracker(
        path=tree_path, local_id=1, tree_stem="hello"
    )

    # 2. First Turn (P1 -> R1)
    p1 = generate_mock_prompt(1, "Fix the data pipeline.")
    r1 = generate_mock_response(1, p1.unique_id, "Pipeline fixed with polars.")

    tree.attach(p1)
    tree.attach(r1)

    # Manually stitch the edge for the mock (normally handled by a Sprout/Flow controller)
    tree.dag.edges.append(
        ConversationEdge(source=p1.unique_id, target=r1.unique_id)
    )

    # 3. Second Turn (P2)
    p2 = generate_mock_prompt(2, "Optimize the DAG traversal.")
    tree.attach(p2)
    tree.dag.edges.append(
        ConversationEdge(source=r1.unique_id, target=p2.unique_id)
    )

    # Ensure graph syncs if using your current Pydantic revalidation approach
    tree.dag = tree.dag.model_validate(tree.dag.model_dump())

    logger.success(f"Tree DAG constructed with {len(tree.dag.nodes)} nodes.")

    # 4. Sprout Extraction Test
    logger.info("Extracting Sprout from R1...")
    sprout = tree.find_conversation_by_stem(
        stems=[p1.stem, r1.stem], target_uuid=r1.unique_id
    )

    assert len(sprout.dag.nodes) == 2, (
        "Sprout should contain R1 and its successor P2"
    )
    logger.success("Sprout extracted successfully!")

    # 5. Simulate Sprout Return (R2 generated offline/remotely)
    r2 = generate_mock_response(2, p2.unique_id, "DAG optimization complete.")
    sprout.responses[r2.unique_id] = r2

    # Add new node and edge to the Sprout DAG
    sprout.dag.nodes.append(
        ConversationNode(id=r2.unique_id, partition="R", local_id=2)
    )
    sprout.dag.edges.append(
        ConversationEdge(source=p2.unique_id, target=r2.unique_id)
    )

    # 6. Re-attach Sprout to Master Tree
    logger.info("Attaching Sprout back to Master DAG...")
    tree.dag.attach_sprout(parent_uuid=r1.unique_id, sprout_dag=sprout.dag)

    logger.success(f"Final Master DAG nodes: {len(tree.dag.nodes)}")
    logger.success(f"Topological sort: {tree.dag.topological_sort()}")


if __name__ == "__main__":
    run_mock_workflow()
