import uuid

from loguru import logger

from ...config import SachmisConfig, get_config
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

        logger.info(f"DAG attached from Tree to {self.__class__.__name__}")
        self._print_extracted_dag()

    def _print_extracted_dag(self):
        config: SachmisConfig = get_config()
        if config.defaults.debug.print_at_tree_extract:
            printer.special("Tree DAG")
            printer(self._dag_of_entire_tree)
            printer.special("Sprout DAG")
            printer(self._growing_dag)
        if config.defaults.debug.pause_at_tree_extract:
            input()

    def prepare_package(self, selection: SelectedSproutData) -> SproutPackage:
        """Load SproutPackage with everything needed sfor a new DAG"""

        logger.debug(f"Creating package for {selection=}")

        if selection.sprout_id == 0:  # case root (or fail)
            previous_response_id = None
            previous_remote_id = None

        elif node := self.tree_dag.find_previous_model_response_from_sprout(
            selection.model, selection.sprout_id
        ):
            previous_response_id: str = node.response.unique_id
            previous_remote_id: str = node.response.remote_id

        else:
            raise SachmisDataError(f"Missing Selected Model: {selection=}")

        next_response_id: str = str(uuid.uuid4())
        # TASK: figure out how to ensure previous_response_id-chain
        self._sprout_registry[next_response_id] = previous_response_id
        logger.debug(
            "attached to sprout_registry:\n"
            f"{next_response_id=}\n{previous_response_id=}"
        )

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

        # TEST:

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
