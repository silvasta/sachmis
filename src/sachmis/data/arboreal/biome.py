from collections.abc import Callable
from enum import StrEnum, auto
from pathlib import Path
from typing import Self

from loguru import logger
from pydantic import Field
from sstcore.data.files import SstFile
from sstcore.utils import day_count

from ...config import config
from .base import Arboreal, ArborealTracker
from .forest import Forest


class BiomeStatus(StrEnum):
    STARTED = auto()
    OK = auto()
    FAIL_OBSERVE = auto()
    FAIL_CREATE = auto()
    CREATED = auto()
    PROMPT = auto()


class Biome(Arboreal[Forest]):
    """Global Master Forest, Registry for entire Content"""

    responses: list[SstFile] = Field(default_factory=list)

    @property
    def n_responses(self) -> int:
        return len(self.responses)

    def attach_new_full_response(self, text: str, path: Path) -> None:
        """Setup File tracker with relative path to full response dir"""

        path.write_text(text)
        response: SstFile = SstFile(local_path=Path(path.name))

        self.responses.append(response)

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Biome - Custom Functions
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    @classmethod
    def with_name(cls, name: str | None = None) -> Self:
        logger.info("Create new Biome")

        biome_filename: str = (
            config().names.biome_file if name is None else name
        )
        biome_file: Path = config().paths.new_biome_file(biome_filename)

        biome: Biome = cls.create_with_tracker(
            path=biome_file, local_id=day_count()
        )
        logger.success("Biome created!")

        biome.save_state(file=biome_file, lock_required=False)
        biome.apply_to_config(biome_file)

        return biome

    def apply_to_config(self, biome_file: Path):
        logger.info("Merge changes back to Settings file")

        if biome_file.name == config().names.biome_file:
            logger.debug("path from Names already active in Biome")
        else:
            config().names.biome_file = biome_file.name
            config().save_settings()
            logger.info(f"Updated active Biome in Names to {biome_file.name}")

        logger.success(f"{self.tracker} Active Biome! {biome_file=}")

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Arboreal - Access to Members
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    # LATER: Biome Registry? Maybe while SQModel refactor

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

    def attach_new_forest(self, forest_file: Path) -> ArborealTracker:
        local_id: int = self._next_instance_id()
        new_forest: Forest = self._setup_forest(forest_file, local_id)
        new_forest.save_state(forest_file, lock_required=False)

        return self.attach_forest(
            forest=new_forest, forest_file=forest_file, local_id=local_id
        )

    def _setup_forest(self, forest_file: Path, local_id: int) -> Forest:
        return Forest.with_camp(
            path=forest_file,
            local_id=local_id,
        )

    def attach_forest(
        self, forest: Forest, forest_file: Path, local_id: int
    ) -> ArborealTracker:

        return self.registry.attach(
            arboreal=forest, path=forest_file, local_id=local_id
        )

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Biome - Health checks, maybe -> ArborealDisk?
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    def health_check(self):  # MOVE: base class
        tests: list[Callable] = [
            self.registry.check_tracker_paths_exist,
            self.registry.check_tracker_paths_unique,
        ]  # LATER: better output
        if _no_issues := all(test_ok() for test_ok in tests):
            logger.info("Biome ok")
