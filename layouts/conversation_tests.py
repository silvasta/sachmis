import networkx as nx
from pyvis.network import Network

from sachmis.data.conversation import (
    ConversationDAG,
    ConversationEdge,
    ConversationNode,
)
from sachmis.utils import printer


def main():
    manual_1()
    # dag: ConversationDAG = run_robustness_test()
    # dag.draw()
    # draw_interactive_pyvis(dag)


def manual_1():
    name: str = "tree_zero"
    root_prompt = ConversationNode(
        id="fff", partition="P", local_id=1, name=name
    )
    nodes: list[ConversationNode] = [root_prompt]
    edges: list[ConversationEdge] = []

    dag = ConversationDAG(nodes=nodes, edges=edges)

    response_1_1 = ConversationNode(
        id="aaa", partition="R", local_id=1, name=name
    )
    response_1_2 = ConversationNode(
        id="aab", partition="R", local_id=2, name=name
    )
    response_1_3 = ConversationNode(
        id="aac", partition="R", local_id=3, name=name
    )
    dag.edges.extend(
        [
            ConversationEdge(source=root_prompt.id, target=response_1_1.id),
            ConversationEdge(source=root_prompt.id, target=response_1_2.id),
            ConversationEdge(source=root_prompt.id, target=response_1_3.id),
        ]
    )
    dag.nodes.extend([response_1_1, response_1_2, response_1_3])

    prompt_2 = ConversationNode(id="gff", partition="P", local_id=2, name=name)
    dag.nodes.extend([prompt_2])

    response_2_1 = ConversationNode(
        id="hff", partition="R", local_id=4, name=name
    )
    response_2_2 = ConversationNode(
        id="iff", partition="R", local_id=5, name=name
    )
    dag.nodes.extend([response_2_1, response_2_2])

    dag.edges.extend(
        [
            ConversationEdge(source=response_1_1.id, target=prompt_2.id),
            ConversationEdge(source=prompt_2.id, target=response_2_1.id),
            ConversationEdge(source=prompt_2.id, target=response_2_2.id),
        ]
    )
    dag: ConversationDAG = dag.model_validate(dag.model_dump())
    printer(dag)

    print(dag.topological_sort())
    dag.draw()
    printer.title("Before Extraction")

    # way_1(dag)
    way_2(dag)


def way_1(dag):
    """Fail for Re-Attach, same id, somehow merge?"""
    name = "way1"
    sprout: ConversationDAG = dag.copy_subtree("hff")
    printer(sprout)

    prompt_3 = ConversationNode(id="rrr", partition="P", local_id=3, name=name)
    prompt_4 = ConversationNode(id="ttt", partition="P", local_id=4, name=name)

    response_3 = ConversationNode(
        id="rrt", partition="R", local_id=6, name=name
    )
    sprout.attach_leaf("hff", prompt_3)
    sprout.attach_leaf("hff", prompt_4)
    sprout.attach_leaf("rrr", response_3)
    printer(sprout)
    sprout: ConversationDAG = sprout.model_validate(sprout.model_dump())
    sprout.draw()
    tree: ConversationDAG = dag.attach_sprout("hff", sprout)
    print(tree)
    tree.draw()


def way_2(dag):
    prompt_3: ConversationDAG = dag.extract_sprout("iff", "topic_a")
    prompt_4: ConversationDAG = dag.extract_sprout("iff", "topic_a")

    print(prompt_3)
    print(prompt_4)

    # IDEA: use new class with 1 attribute more, the future edge
    # - or just check the ID where to attach, store this, attach at the end


def run_robustness_test():
    print("--- STEP 1: Creating Initial Master DAG ---")
    name = "tree_zero"

    # Root P-node
    root = ConversationNode(id="fff", partition="P", local_id=1, name=name)

    # Layer 1 R-nodes
    r1 = ConversationNode(id="aaa", partition="R", local_id=1, name=name)
    r2 = ConversationNode(id="aab", partition="R", local_id=2, name=name)
    r3 = ConversationNode(id="aac", partition="R", local_id=3, name=name)

    dag = ConversationDAG(
        nodes=[root, r1, r2, r3],
        edges=[
            ConversationEdge(source=root.id, target=r1.id),
            ConversationEdge(source=root.id, target=r2.id),
            ConversationEdge(source=root.id, target=r3.id),
        ],
    )

    # STEP 2: Mutate the graph and correctly perform revalidation
    print("Mutating structural elements in-place...")
    p2 = ConversationNode(id="gff", partition="P", local_id=2, name=name)
    r2_1 = ConversationNode(id="hff", partition="R", local_id=2, name=name)
    r2_2 = ConversationNode(id="iff", partition="R", local_id=2, name=name)

    dag.nodes.extend([p2, r2_1, r2_2])
    dag.edges.extend(
        [
            ConversationEdge(source=r1.id, target=p2.id),
            ConversationEdge(source=p2.id, target=r2_1.id),
            ConversationEdge(source=p2.id, target=r2_2.id),
        ]
    )

    # Revalidate and RE-ASSIGN!
    dag = ConversationDAG.model_validate(dag.model_dump())

    print("Topological sort matches expected structure:")
    print(dag.topological_sort())

    # Test visualization
    dag.draw()

    # --- STEP 3: Subtree Extraction ("R" node extraction) ---
    print("\n--- STEP 4: Extracting Subtree from 'aaa' (R-node) ---")
    # Subtree should include 'aaa' -> 'gff' -> ('hff', 'iff')
    sub_tree = dag.copy_subtree("aaa")
    print(f"Subtree Nodes: {[n.id for n in sub_tree.nodes]}")
    assert "iff" in [n.id for n in sub_tree.nodes], "Recursive descent failed."

    # --- STEP 4: Save & Load via JSON Serialization ---
    print("Serializing Subtree to JSON and rebuilding...")
    serialized_json = sub_tree.model_dump_json()
    _loaded_sub_tree = ConversationDAG.model_validate_json(serialized_json)

    # --- STEP 5: Sprout Attachment back into Master DAG ---
    print("\n--- STEP 6: Attaching Sprout onto target Node ('aab') ---")
    # Let's create a new sprout with custom nodes to append to 'aab'
    new_p = ConversationNode(id="new_p", partition="P", local_id=9)
    new_r = ConversationNode(id="new_r", partition="R", local_id=9)
    sprout = ConversationDAG(
        nodes=[new_p, new_r],
        edges=[ConversationEdge(source=new_p.id, target=new_r.id)],
    )

    # Attach the sprout back onto the 'aab' node of the master DAG
    updated_master = dag.attach_sprout(parent_id="aab", sprout_dag=sprout)

    print("New master node IDs after sprout attachment:")
    print([n.id for n in updated_master.nodes])

    return updated_master
    # IMPORTANT:
    # updated_master.draw()
    # draw_interactive_pyvis(updated_master)
    # export_vector_graph(updated_master)

    # INFO: uv add pyvis


def draw_interactive_pyvis(dag: ConversationDAG, filename="dag.html"):
    net = Network(
        directed=True,
        height="750px",
        width="100%",
        bgcolor="#222222",
        font_color="white",
    )

    # Set physics solver tailored to trees
    net.barnes_hut(gravity=-4000, central_gravity=0.3, spring_length=95)

    for node in dag.nodes:
        color = "#1E90FF" if node.partition == "P" else "#32CD32"
        label = f"[{node.partition}] {node.id}\n{node.name}"
        net.add_node(node.id, label=label, color=color, shape="ellipse")

    for edge in dag.edges:
        net.add_edge(edge.source, edge.target, color="#888888")

    net.show(filename, notebook=False)


# INFO: Requires: sudo apt-get install graphviz && pip install pygraphviz
# sudo apt install python3-pygraphviz # BROKEN
def export_vector_graph(dag: ConversationDAG, output_filename="graph"):
    # Convert networkx representation to pygraphviz
    agraph = nx.nx_agraph.to_agraph(dag.graph)

    # Customize layout parameters for vertical tree orientation (Top-Down)
    agraph.graph_attr.update(rankdir="TB", nodesep="0.5", ranksep="0.75")
    agraph.layout(prog="dot")

    # Save SVG/PDF format
    agraph.draw(f"{output_filename}.svg")
    print(f"Exported system tree to {output_filename}.svg")


if __name__ == "__main__":
    main()
