from pathlib import Path

from loguru import logger
from pydantic import Field
from silvasta.data.files import SstFile

from .base import ArborealDisk, ArborealTracker
from .forest import Forest


class Biome(ArborealDisk[Forest]):
    """Global Master Forest, registry for entire content"""

    responses: list[SstFile] = Field(default_factory=list)

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Arboreal - Access to Members
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    @property
    def n_forest(self) -> int:
        return self.n_children

    @property
    def forests(self) -> list[ArborealTracker]:
        """Serialized part of registry with UUID and ArborealTracker"""
        return self._registry.all_trackers

    @property
    def loaded_forests(self) -> list[Forest]:
        return self._registry.all_members

    @property
    def missing_forests(self) -> list[ArborealTracker]:
        return self._registry.tracker_with_invalid_paths

    def n_trees(self) -> int:
        return sum(forest.n_trees for forest in self.loaded_forests)

    def n_sprouts(self) -> int:
        return sum(forest.n_sprouts for forest in self.loaded_forests)

    def attach_forest(
        self, forest: Forest, forest_file: Path
    ) -> ArborealTracker:
        return self._attach(forest, forest_file)

    def attach_new_forest(self, forest_file: Path) -> Forest:
        new_forest = Forest()
        new_forest.save_state(forest_file)
        self.attach_forest(forest=new_forest, forest_file=forest_file)

        return new_forest

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Biome - Health checks, maybe -> ArborealDisk?
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    def health_check(self):
        # LATER: check other problems that will occur
        # - handle cases that occur often specific, heal/repair
        if all(
            (
                self._check_tracker_paths_exist(),
                self._check_tracker_paths_unique(),
            )
        ):
            logger.info("Biome ok")

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Biome - Custom Functions
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    @property
    def n_responses(self) -> int:
        return len(self.responses)

    def attach_new_full_response(self, text: str, path: Path) -> None:
        """Setup File tracker with relative path to full response dir"""

        response: SstFile = SstFile(local_path=Path(path.name))
        path.write_text(text)

        self.responses.append(response)
