import uuid

from loguru import logger
from sstcore.utils.paint import ColorBox

from ...exceptions import SachmisDataError
from ...utils import printer
from ..arboreal import ArborealTracker, Tree
from ..conversation import Prompt, Response, SelectedSproutData, SproutDAG
from ..conversation.dag import ResponseNode
from ..conversation.fusion import SproutPackage


class DataHandler:
    _tree_tracker: ArborealTracker[Tree] | None = None
    _initial_prompt: Prompt | None = None

    _dag_of_entire_tree: SproutDAG | None = None
    _growing_dag: SproutDAG | None = None

    _sprout_registry: dict[str, str | None] = {}  # [next, prev]

    def __init__(self, tracker: ArborealTracker[Tree]):
        self._tree_tracker: ArborealTracker[Tree] = tracker

    @property
    def tree_tracker(self) -> ArborealTracker[Tree]:
        if not self._tree_tracker:
            raise SachmisDataError("Missing Tracker!")
        return self._tree_tracker

    @property
    def tree_id(self) -> int:
        return self.tree_tracker.local_id

    @property
    def prompt(self) -> Prompt:
        if not self._initial_prompt:
            raise SachmisDataError("No Initial Prompt loaded, wait for Tree")
        return self._initial_prompt

    @property
    def growing_dag(self) -> SproutDAG:
        if not self._growing_dag:
            raise SachmisDataError("No DAG loaded, can't provide DAG")
        return self._growing_dag

    @property
    def tree_dag(self) -> SproutDAG:
        if not self._dag_of_entire_tree:
            raise SachmisDataError("No DAG loaded, can't provide DAG")
        return self._dag_of_entire_tree

    def extract_data_from_tree(self, tree: Tree, topic: str, prompt_text: str):
        """Transform Tree Data to new Prompt and setup DAG"""

        self._initial_prompt: Prompt = Prompt.from_text(
            content=prompt_text,
            sprout_id=tree.next_sprout_id(),
            topic=topic,  # LATER: check when to extract/slugify
            tree_id=self.tree_id,
        )
        self._dag_of_entire_tree: SproutDAG = tree.export_dag()
        self._growing_dag: SproutDAG = SproutDAG.init(self._initial_prompt)

        logger.debug(f"result: {self}")
        self._print_extracted_dag()

    def _print_extracted_dag(self):
        printer(self._cli)
        # printer.debug("Tree DAG", self.tree_dag._cli)
        # printer.debug("Sprout DAG", self.growing_dag._cli, stop=True)  # NEXT:

    def prepare_package(self, selection: SelectedSproutData) -> SproutPackage:
        """Load SproutPackage with everything needed for a new DAG"""

        # NEXT: selection->data
        # NEXT: selection->data
        # NEXT: selection->data
        # NEXT: selection->data
        # NEXT: selection->data
        logger.debug(f"Creating package for {selection=}")

        if selection.sprout_id == 0:  # case root (or fail)
            previous_response_id = None
            previous_remote_id = None

        elif node := self.tree_dag.find_previous_model_response_from_sprout(
            selection.model, selection.sprout_id
        ):
            previous_response_id: str = node.response.unique_id
            previous_remote_id: str = node.response.remote_id

        else:  # TODO: here below, a bit confusing?
            raise SachmisDataError(f"Missing Selected Model: {selection=}")

        next_response_id: str = str(uuid.uuid4())
        self._sprout_registry[next_response_id] = previous_response_id
        logger.debug(
            "attached to sprout_registry:\n"
            f"{next_response_id=}\n{previous_response_id=}"
        )
        # REFACTOR: package with everything and only everything that is needed
        return SproutPackage(
            model=selection.model,
            prompt=self.prompt,
            next_response_id=next_response_id,
            previous_response_id=previous_response_id,
            previous_remote_id=previous_remote_id,
        )

    def handle_response(self, response: Response):
        """Process the received Prompt or Response with your Schema"""

        logger.info(f"Handling {response=}")

        if response.unique_id not in self._sprout_registry:
            # TASK: create special Error: handle response temp_bak_file
            raise SachmisDataError("Failed Response ID handling...")

        new_node: ResponseNode = ResponseNode.from_response(response)
        self.growing_dag.attach_leaf(self.prompt.unique_id, new_node)

    def attach_data_back(self, tree: Tree):
        """Send the new created part of the DAG to the Tree"""

        self._print_extracted_dag()

        if len(tree.dag.nodes) == 0:
            tree.dag = self.growing_dag
            logger.success("Attached new DAG to empty Tree")
        else:
            previous: list[str] = [
                v for v in self._sprout_registry.values() if v
            ]
            match n_previous := len(previous):
                case 0:
                    logger.error(self._sprout_registry)
                    raise ValueError("Missing previous id")
                case _:
                    response_to_attach: str = previous.pop()
                    logger.debug(f"found {n_previous=}")

            tree.attach_sub_dag(
                response_to_attach,
                self.growing_dag.model_copy(),
            )
            logger.success("DAG is back home")

    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
    ### START of Representation
    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --

    def __repr__(self):
        handler: str = type(self).__name__

        # IDEA: merge getattr into return f-strings?
        # - or completely avoid getattr?
        tree_tracker = getattr(self, "_tree_tracker", None)
        initial_prompt = getattr(self, "_initial_prompt", None)
        dag_of_entire_tree = getattr(self, "_dag_of_entire_tree", None)
        growing_dag = getattr(self, "_growing_dag", None)
        sprout_registry = getattr(self, "_sprout_registry", {})

        return (  # LATER: check for loop over handlers, check {_handler!r}
            f"{handler}("
            f"_tree_tracker={tree_tracker}, "
            f"_initial_prompt={initial_prompt}, "
            f"_dag_of_entire_tree={dag_of_entire_tree}, "
            f"_growing_dag={growing_dag}, "
            f"_sprout_registry={sprout_registry}"
            f")"
        )

    def __str__(self) -> str:
        return self._assemble_str()

    def _assemble_str(self, tree_dag="", internal_dag="", handler=""):
        _handler: str = handler or type(self).__name__
        _tree_dag = tree_dag or self._tree_dag_name()
        _internal_dag = internal_dag or self._internal_dag_name()
        return f"{_handler}({_tree_dag} and {_internal_dag})"

    @property
    def colorful(self) -> str:  # TODO: colorful as styled_name
        c: ColorBox = ColorBox.with_mode("bold")
        handler: str = c.red(type(self).__name__)
        tree_dag: str = c.green(self._tree_dag_name(color=True))
        internal_dag: str = c.green(self._internal_dag_name(color=True))
        return self._assemble_str(tree_dag, internal_dag, handler)

    # @property
    # def _cli(self) -> str:
    #     c: ColorBox = ColorBox.with_mode("bold")
    #     handler: str = c.red(type(self).__name__)
    #     tree_dag: str = c.green(self._tree_dag_name(color=True))
    #     internal_dag: str = c.green(self._internal_dag_name(color=True))
    #     return f"{handler}(\n{tree_dag}\nand\n{internal_dag})"
    # IDEA: use like multiline formatting:
    #   DataHandler(
    #       TreeDag
    #           and
    #       GrowingDag
    # )

    @property
    def _cli(self) -> str:  # TODO: colorful as styled_name
        return self.colorful

    def _tree_dag_name(self, color=False) -> str:

        return f"Tree_{self.tree_id}{_surrounding(self._tree_dag_str(color))}"

    def _internal_dag_name(self, color=False) -> str:
        return f"Internal{_surrounding(self._internal_dag_str(color))}"

    def _tree_dag_str(self, color=False) -> str:
        if self._dag_of_entire_tree is None:
            return "N/A"
        if not color:
            return str(self._dag_of_entire_tree)
        return self._dag_of_entire_tree._cli

    def _internal_dag_str(self, color=False) -> str:
        if self._growing_dag is None:
            return "N/A"
        if not color:
            return str(self._growing_dag)
        return self._growing_dag._cli

    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
    ### END of Representation
    ### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


# WARN: END OF CLASS WAS BEFORE
# MOVE: somewhere
def _surrounding(inside: str) -> str:
    return "{{" + inside + "}}"
