from contextlib import AbstractContextManager

from loguru import logger

from ...config import SachmisConfig, get_config
from ...data import DataManager
from ...data.arboreal import ArborealTracker, Tree


class TreeExtractor(AbstractContextManager):
    """Ensure Tree Data is loaded at start and saved at exit"""

    def __init__(self, data: DataManager):

        # LATER: check moving load after selection

        logger.debug("Loading Tree...")
        self.data: DataManager = data

        with Tree.edit_mode(path := data.handler.tree_tracker.path) as tree:
            self.tracker: ArborealTracker = tree.sample_tracker(
                path, local_id=data.handler.tree_tracker.local_id
            )
            self.data.handler.attach_tree_data(
                sprout_id=tree.next_sprout_id(),
                full_dag=tree.export_dag(),
            )
        # NEXT: no data_dag to Tree???
        # NEXT: no data_dag to Tree???
        logger.debug("Tree Data extracted - Closing Tree for now...")

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        config: SachmisConfig = get_config()
        logger.debug("...Tree Extractor ")

        if exc_type is not None:  # LATER: what can happen?
            logger.warning(f"Task failed with {exc_type.__name__}")
            return config.defaults.context.tree_error.swallow

        logger.debug("Loading Tree...")
        with Tree.edit_mode(self.tracker.path) as tree:
            tree.attach_to_dag(self.data.handler.export_dag())

        logger.debug("Tree closed - Data transferred back")
        return config.defaults.context.tree_end.swallow
