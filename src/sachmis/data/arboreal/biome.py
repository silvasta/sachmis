from collections.abc import Callable
from pathlib import Path

from loguru import logger
from pydantic import Field
from sstcore.data.files import SstFile

from ...config import SachmisConfig, get_config
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

    @classmethod
    def with_name(cls, name: str | None = None):
        logger.info("Create new Biome")
        config: SachmisConfig = get_config()

        biome_filename: str = config.names.biome_file if name is None else name
        biome_file: Path = config.paths.new_biome_file(biome_filename)

        # LATER: Biome Registry? Maybe while SQModel refactor

        biome: Biome = cls.create_with_tracker(
            path=biome_file, local_id=config.paths.num_biome_files + 1
        )
        logger.success("Biome created!")

        biome.save_state(file=biome_file, lock_required=False)
        biome.apply_to_config(biome_file)

    def apply_to_config(self, biome_file: Path):
        logger.info("Merge changes back to Settings file")
        config: SachmisConfig = get_config()

        if biome_file.name == config.names.biome_file:
            logger.debug("path from Names already active in Biome")
        else:
            config.save_settings()
            logger.info(f"Updated active Biome in Names to{biome_file.name}")

        logger.success(f"{self.tracker_info.stat} Active Biome! {biome_file=}")

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

    @classmethod
    def check_filesystem(cls) -> bool:
        config: SachmisConfig = get_config()

        num_biome_files: int = config.paths.num_biome_files
        logger.info(f"Found {num_biome_files=} in {config.paths.biome_dir=}")

        biome_files: set[Path] = config.paths.biome_files
        logger.debug(f"current status: {biome_files=}")

        if num_biome_files > 0:
            return True
        else:
            return False

    def health_check(self):
        tests: list[Callable] = [
            self.registry.check_tracker_paths_exist,
            self.registry.check_tracker_paths_unique,
            self.check_filesystem,
        ]  # LATER: better output
        if _no_issues := all(test_ok() for test_ok in tests):
            logger.info("Biome ok")
