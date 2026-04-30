from pathlib import Path
from typing import Self

from loguru import logger

from ...exceptions import SproutRegistryError
from ..prompt import Prompt
from ..response import Response
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
        return self.registry.all_trackers

    @property
    def local_sprout_ids(self) -> list[int]:
        return [s.local_id for s in self.registry.all_trackers]

    def get_sprout_by_unique_id(self, id: str) -> Sprout:
        tracker: ArborealTracker = self.registry.get_tracker(id)
        return self.get_sprout_by_path(tracker.path)

    # MOVE: maybe close to Sprout._next_sprout_locator as backwards function
    def get_sprout_by_path(self, path: Path) -> Sprout:
        logger.debug(f"walkig tree for sprout with id: {path=}")
        current_node: Sprout = self.sprout
        try:
            for next_node_num in path.parts:
                next_id: int = int(next_node_num) - 1
                current_node: Sprout = current_node.sprouts[next_id]
        except ValueError, IndexError:
            raise SproutRegistryError(
                f"Invalid number for Sprout list access: {path=}"
            ) from None

        return current_node

    def find_previous_sprout(self, sprout: Sprout) -> Sprout | None:
        if sprout.unique_id == self.sprout.unique_id:
            raise SproutRegistryError("Master Tree Sprout not allowed here..")
        try:
            parent_path: Path = sprout.sprout_locator.parent
            return self.get_sprout_by_path(parent_path)
        except SproutRegistryError as err:
            msg = f"Unable to locate parent of Sprout: {sprout.sprout_locator}"
            logger.error(f"{msg}\n{err}")
        return None

    def attach_sprout(self, sprout: Sprout) -> ArborealTracker:
        return self._attach(instance=sprout, path=sprout.sprout_locator)

    def attach_new_sprout(
        self, existing_sprout: Sprout, model: str, prompt: Prompt
    ) -> Sprout:
        new_sprout: Sprout = existing_sprout.attach_sprout_to_sprout(
            model=model,
            prompt=prompt,
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

    @classmethod
    def create_with_sprout(
        cls, model: str, prompt: Prompt, tree_stem: str = ""
    ) -> Self:
        """Create new Tree wich only exist with exatly 1 Sprout (with own Sprouts >=0)"""
        sprout: Sprout = Sprout(
            model=model,
            prompt=prompt,  # TODO: empty prompt or so?
            response=None,
            sprout_locator=Path(),
            previous_response_id="",
        )
        tree_stem: str = tree_stem or prompt.slug_topic
        tree: Self = cls(
            model=model,
            tree_stem=tree_stem,
            sprout=sprout,
        )
        tree.attach_sprout(sprout)

        return tree

    def provide_sprout(
        self, sprout_locator: str, model: str, prompt: Prompt
    ) -> Sprout:
        logger.warning(f"SO FAR: ignoring {sprout_locator=}")
        sprout_parent: Sprout = self.sprout  # PARAM:
        return self.attach_new_sprout(  # NEXT: find proper sprout
            existing_sprout=sprout_parent, model=model, prompt=prompt
        )

    @classmethod
    def extract_sprout(
        cls, tree_file: Path, sprout_locator: str, model: str, prompt: Prompt
    ) -> Sprout:
        """Just quickly open the Tree, extract new uncompleted sprout, later load and add completed"""

        logger.info("Loading Tree to extract new Sprout")

        with cls.edit_mode(tree_file) as tree:
            new_sprout: Sprout = tree.provide_sprout(
                sprout_locator, model=model, prompt=prompt
            )
            new_sprout.set_extracted()

        return new_sprout

    @classmethod
    def reattach_sprout(cls, tree_file: Path, sprout: Sprout):
        """Just quickly open the Tree, extract new uncompleted sprout, later load and add completed"""

        logger.info("Loading Tree to reattch Sprout information")

        with cls.edit_mode(tree_file) as tree:
            tree_sprout: Sprout = tree.get_sprout_by_unique_id(
                sprout.unique_id
            )
            if not (tree_sprout.extracted_at == sprout.extracted_at):
                logger.warning(
                    f"{tree_sprout.extracted_at=} not {sprout.extracted_at=}!"
                )
            tree_sprout.response: Response = sprout.completed_response
            tree_sprout.loaded_at = sprout.loaded_at
            tree_sprout.started_at = sprout.started_at
            tree_sprout.completed_at = sprout.completed_at

        logger.info("All information submitted, Tree closed")

    # TASK: build sprout tree
