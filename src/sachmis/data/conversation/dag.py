from sstcore.utils import SimpleTreeNode


class SproutNode(SimpleTreeNode):
    pass


# def build_conversation_tree(
#     root_sprout: Conversation,
#     target: Literal[uuid, local] = "uuid",
# ) -> SproutNode:
#
#     return _recursive_conversation_tree(
#         current_sprout=root_sprout, visited=set(), target=target
#     )
#
#
# def _recursive_conversation_tree(
#     current_sprout: Conversation,
#     visited: set[str],
#     target: Literal[uuid, local] = "uuid",
# ) -> SproutNode:
#
#     if current_sprout.unique_id in visited:
#         raise SachmisDataError(f"Cylce in Tree! {current_sprout.desc}")
#
#     visited.add(current_sprout.unique_id)
#
#     if not current_sprout.get_successor():
#         return current_sprout.as_tree_node(target=target)
#
#     branch_nodes: list[ConversationTreeNode] = []
#
#     for next_branch in current_sprout.get_successor():
#         branch_nodes.append(
#             _recursive_conversation_tree(
#                 current_sprout=next_branch,
#                 visited=visited,
#                 target=target,
#             )
#         )
#
#     return current_sprout.as_tree_node(branch_nodes)
