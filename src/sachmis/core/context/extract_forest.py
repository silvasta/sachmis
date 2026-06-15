from contextlib import AbstractContextManager

from loguru import logger

from ...config import SachmisConfig, get_config
from ...data import DataManager
from ...data.arboreal import ArborealTracker, Forest
from ...data.camp import CampManager


class ForestExtractor(AbstractContextManager):
    """Ensure Forest Data is loaded at start and saved at exit"""

    def __init__(self, data: DataManager):
        config: SachmisConfig = get_config()

        logger.debug("Loading Forest...")
        self.data: DataManager = data

        with Forest.edit_mode(path := config.paths.forest_file) as forest:
            self.tracker: ArborealTracker = forest.sample_tracker(path)

            self.tree_tracker: ArborealTracker = (
                forest.provide_tree(tree_id)
                if (tree_id := data.handler.scanned_tree_id)
                else forest.attach_new_tree(data.handler.topic)
            )
            data.handler.attach_tracker(self.tree_tracker)

            self.camp: CampManager = forest.get_camp()
            data.attach_camp(self.camp)

        logger.debug("Forest Data extracted - Closing Forest for now...")

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        config: SachmisConfig = get_config()
        logger.debug("...Forest Extractor 󱢗")

        if exc_type is not None:  # LATER: what can happen?
            logger.warning(f"Task failed with {exc_type.__name__}")
            return config.defaults.context.forest_error.swallow

        logger.debug("Loading Forest...")
        with Forest.edit_mode(self.tracker.path) as forest:
            forest.attach_camp_back_by_mirror(self.camp)
            # LATER: confirm Tree, maybe after first response is written

        logger.debug("Forest closed - Data transferred back")
        return config.defaults.context.forest_end.swallow
