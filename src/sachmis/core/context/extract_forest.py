from contextlib import AbstractContextManager

from loguru import logger

from ...config import config
from ...data import DataManager
from ...data.arboreal import ArborealTracker, Forest, Tree


class ForestExtractor(AbstractContextManager):
    """Ensure Forest Data is loaded at start and saved at exit"""

    def __init__(self, data: DataManager):

        logger.debug("Loading Forest...")
        self.data: DataManager = data

        with Forest.edit_mode(path := config().paths.forest_file) as forest:
            self.tracker: ArborealTracker[Forest] = forest.sample_tracker(path)

            tree_tracker: ArborealTracker[Tree] = (
                forest.provide_tree(tree_id)
                if (tree_id := data.front.scanned_tree_id)
                else forest.attach_new_tree(data.front.topic)
            )
            data.attach_handler(tree_tracker)
            data.attach_camp(forest.get_camp())

        logger.debug("Forest Data extracted - Closing Forest for now...")

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        logger.debug("...Forest Extractor 󱢗")

        if exc_type is not None:  # LATER: what can happen?
            logger.warning(f"Task failed with {exc_type.__name__}")
            return config().defaults.context.forest_error.swallow

        logger.debug("Loading Forest...")
        with Forest.edit_mode(self.tracker.path) as forest:
            forest.attach_camp_back_by_mirror(self.data.camp)
            # LATER: confirm Tree(id), maybe after first response written?

        logger.debug("Forest closed - Data transferred back")
        return config().defaults.context.forest_end.swallow
