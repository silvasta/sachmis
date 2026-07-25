from collections.abc import Callable
from pathlib import Path
from typing import Self

from loguru import logger
from pydantic import Field
from sstcore.data.files import SstFile
from sstcore.utils import day_count

from sachmis.config import SachmisConfig

from ...exceptions import ArborealTrackingError
from .base import Arboreal, ArborealTracker
from .forest import Forest


class Biome(Arboreal[Forest]):
    """Global Master Forest, Registry for entire Content"""

    responses: list[SstFile] = Field(default_factory=list)

    @property
    def n_responses(self) -> int:
        """Show number of tracked full responses"""
        return len(self.responses)

    def attach_new_full_response(self, text: str, path: Path) -> None:
        """Attach with tracker and relative path inside full response dir"""
        path.write_text(text)
        response: SstFile = SstFile(local_path=Path(path.name))
        self.responses.append(response)

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Biome - Custom Functions
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    @classmethod
    def named(cls, config: SachmisConfig, name: str | None = None) -> Self:
        """Create new Biome and set as active Biome in config.Names"""
        logger.info("Create new Biome")  # TODO: emit, or move to caller

        biome_file: Path = config.paths._biome_file(name)

        if biome_file in config.paths.biome_files:
            raise ArborealTrackingError(
                biome_file, issue="Exists", arbo="Biome"
            )
        biome: Biome = cls.create_with_tracker(
            path=biome_file, local_id=day_count()
        )
        logger.success("Biome created!")  # TODO: emit, maybe in Base

        biome.save_state(file=biome_file, lock_required=False)
        biome.set_active(biome_file, config)  # LATER: as option?

        return biome

    def set_active(self, biome_file: Path, config: SachmisConfig):
        """Sync as active Biome in serialized config.settings.Names"""
        logger.info("Merge changes back to Settings file")  # TODO: emit?

        if biome_file.name == config.names.biome_file:
            logger.debug("Biome Name is already set in config.Names")
        else:  # NOTE: log here probably important, idea: move func to config?
            config.names.biome_file = biome_file.name
            config.save_settings()
            self.touch()
            logger.info(f"Updated active Biome in Names: {biome_file.name}")

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
