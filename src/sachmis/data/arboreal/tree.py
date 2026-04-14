from sachmis.utils.exceptions import SproutRegistryError
from pathlib import Path
from typing import Self

from loguru import logger

from ..files import Prompt
from .base import ArborealDisk, ArborealTracker
from .sprout import Sprout


class Tree(ArborealDisk[Sprout]):
    """Top element inside Forest: entry point for every conversation"""

    model: str  # model.unique
    tree_stem: str

    # INFO: all sprouts are tracked in _registry.tracker
    # new attached sprouts are added in _registry._member, but unused
    # sprouts itself are attached to other sprouts, starting at:
    sprout: Sprout  # unique root sprout of all following sprouts

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Arboreal - Access to Members
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    @property
    def n_sprouts(self) -> int:
        return self.sprout.count_all_sprouts

    @property
    def sprouts(self) -> list[ArborealTracker]:
        return self._registry.all_trackers

    @property
    def local_sprout_ids(self) -> list[int]:
        return [s.local_id for s in self._registry.all_trackers]

    def find_tracker_by_unique_id(self, id: str) -> ArborealTracker | None:
        return self._registry.find_tracker(id)

    def get_tracker_by_unique_id(self, id: str) -> ArborealTracker:
        return self._registry.get_tracker(id)

    def get_sprout_by_unique_id(self, id: str) -> Sprout:
        tracker: ArborealTracker = self.get_tracker_by_unique_id(id)
        return self.get_sprout_by_path(tracker.path)

    # MOVE: maybe close to Sprout._next_sprout_locator as backwards function
    def get_sprout_by_path(self, path: Path) -> Sprout:
        logger.debug(f"walkig tree for sprout with id: {path=}")
        current_node: Sprout = self.sprout
        try:
            # str(path) results in "N/N/N/N", str(Path()) in "" -> root catched
            for next_node_num in str(path).split("/"):
                next_id: int = int(next_node_num) - 1
                current_node: Sprout = current_node.sprouts[next_id]
        except (ValueError, IndexError):
            SproutRegistryError(f"Invalid number for list access: {path=}")

        return current_node

    def attach_sprout(self, sprout: Sprout) -> ArborealTracker:
        return self._attach(instance=sprout, path=sprout.sprout_locator)

    def attach_new_sprout(
        self, existing_sprout: Sprout, model: str, prompt: Prompt
    ) -> Sprout:
        new_sprout: Sprout = existing_sprout.attach_sprout_to_sprout(
            model=model, prompt=prompt
        )
        self.attach_sprout(new_sprout)
        return new_sprout

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Tree - Health checks, maybe -> ArborealDisk?
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    # TODO: Tree health
    # - maybe compare sprout walk to registry?
    # - filter invalid sprouts

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Tree - Custom Functions and Atributes
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    def extract_new_sprout_in_edit_mode(
        self,
        tree_file_path: Path,
        existing_sprout_id: str,  # NOTE: alternative sprout.sprout_locator or ArborealTracker of Sprout
        model: str,
        prompt: Prompt,
    ) -> Sprout:
        """Just quickly open the Tree, extract new uncompleted sprout, later load and add completed"""
        with self.__class__.edit_mode(tree_file_path) as tree:
            existing_sprout: Sprout = tree.get_sprout_by_unique_id(
                existing_sprout_id
            )
            sprout: Sprout = tree.attach_new_sprout(
                existing_sprout=existing_sprout, model=model, prompt=prompt
            )
            sprout.set_extracted()
        return sprout

    @classmethod
    def create_with_sprout(
        cls, model: str, prompt: Prompt, tree_stem: str = ""
    ) -> Self:
        """Create new Tree wich only exist with exatly 1 Sprout (with own Sprouts >=0)"""
        sprout: Sprout = Sprout(
            model=model,
            prompt=prompt,
            response=None,
            sprout_locator=Path(),
        )
        tree_stem: str = tree_stem or prompt.slug_topic
        tree: Self = cls(
            model=model,
            tree_stem=tree_stem,
            sprout=sprout,
        )
        tree.attach_sprout(sprout)

        return tree
