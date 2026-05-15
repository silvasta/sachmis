from pathlib import Path

from loguru import logger
from pydantic import Field
from sstcore.data.files import SstFile

from ...data.files import CampManager
from .base import Arboreal, ArborealTracker
from .forest import Forest


class Biome(Arboreal[Forest]):
    """Global Master Forest, Registry for entire Content"""

    responses: list[SstFile] = Field(default_factory=list)

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Biome - Custom Functions
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    @property
    def n_responses(self) -> int:
        return len(self.responses)

    def attach_new_full_response(self, text: str, path: Path) -> None:
        """Setup File tracker with relative path to full response dir"""

        path.write_text(text)
        response: SstFile = SstFile(local_path=Path(path.name))

        self.responses.append(response)

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Arboreal - Access to Members
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    @property
    def n_forest(self) -> int:
        return self.registry.n_trackers

    @property
    def forests(self) -> list[ArborealTracker]:
        """Serialized part of registry with UUID and ArborealTracker"""
        return self.registry.all_trackers

    @property
    def missing_forests(self) -> list[ArborealTracker]:
        return self.registry.tracker_with_invalid_paths()

    # TODO:
    # def n_trees(self) -> int:
    #     return sum(forest.n_trees for forest in self.loaded_forests)

    # TODO:
    # def n_sprouts(self) -> int:
    #     return sum(forest.n_sprouts for forest in self.loaded_forests)

    def attach_new_forest(
        self, forest_file: Path, save=True
    ) -> ArborealTracker:
        new_forest: Forest = self._setup_forest()
        if save:
            new_forest.save_state(forest_file, lock_required=False)
        return self.attach_forest(forest=new_forest, forest_file=forest_file)

    def _setup_forest(self) -> Forest:
        # TASK: how to insert,handle,modify campp???
        camp: CampManager = CampManager()
        new_forest: Forest = Forest.with_camp(camp)
        return new_forest

    def attach_forest(
        self, forest: Forest, forest_file: Path, local_id: int | None = None
    ) -> ArborealTracker:
        if local_id is None:
            local_id: int = self._next_instance_id()

        return self.registry.attach(
            arbo=forest, path=forest_file, local_id=local_id
        )

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Biome - Health checks, maybe -> ArborealDisk?
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    def health_check(self):
        no_issues: bool = all(  # Get True for check fine
            (
                self.registry.check_tracker_paths_exist(),
                self.registry.check_tracker_paths_unique(),
            )
        )
        if no_issues:
            logger.info("Biome ok")

    # LATER: other cases, heal and repair?
