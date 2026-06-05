from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum, auto
from pathlib import Path
from typing import Self

from loguru import logger
from pydantic import Field
from sstcore.data.files import SstFile

from sachmis.exceptions import (
    ArborealFileExistsError,
    ArborealFileMissingError,
)
from sachmis.exceptions.arbo import ArborealFileError

from ...config import SachmisConfig, get_config
from .base import Arboreal, ArborealTracker
from .forest import Forest


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
    @contextmanager
    def observe(cls, obsi: BiomeObserver | None = None):
        """Find Biomes"""
        obsi: BiomeObserver = obsi or BiomeObserver.init()
        config: SachmisConfig = get_config()
        cls.log_filesystem_status()
        try:
            yield obsi
            obsi.set_ok()

        except ArborealFileMissingError as error:
            cls.handle_file_error(error)
            try:
                match config.defaults.cli.missing_biome:
                    case "raise":
                        obsi.set_fail_observe()
                        raise error
                    case "create":
                        cls.with_name()  # TODO: name? prompt?
                        obsi.set_created()
                    case "prompt":
                        obsi.set_prompt()

            except ArborealFileExistsError as error2:
                logger.info(f"Existing {error2.arboreal} File: {error2.file=}")
                cls.handle_file_error(error2)
                obsi.set_fail_create()

        except Exception as unexpected:
            logger.error(f"Biome.observe got {unexpected=}")
            obsi.set_fail_observe()
            raise

    @classmethod
    def log_filesystem_status(cls):
        config: SachmisConfig = get_config()
        logger.debug("start detecting")
        num_biome_files: int = config.paths.num_biome_files
        logger.debug(f"found {num_biome_files=} in {config.paths.biome_dir=}")
        biome_files: set[Path] = config.paths.biome_files
        logger.debug(f"current status: {biome_files=}")

    @classmethod
    def with_name(cls, name: str | None = None):
        logger.info("Create new Biome")
        config: SachmisConfig = get_config()

        biome_filename: str = config.names.biome_file if name is None else name
        biome_file: Path = config.paths.new_biome_file(biome_filename)

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

    @classmethod
    def handle_file_error(cls, error: ArborealFileError):
        assert isinstance(error, ArborealFileError)

        if error.arboreal != "Biome":
            logger.error(f"Biome got {type(error)} from {error.arboreal}")

        # NEXT: find structure, together with Tree,Forest, maybe in Base
        logger.info(f"Conflicting {error.arboreal} File: {error.file=}")
        logger.error(error)  # REMOVE:
        logger.error(error.__class__.__name__)  # REMOVE:

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


class BiomeStatus(StrEnum):
    STARTED = auto()
    OK = auto()
    FAIL_OBSERVE = auto()
    FAIL_CREATE = auto()
    CREATED = auto()
    PROMPT = auto()


@dataclass
class BiomeObserver:
    result: BiomeStatus

    @classmethod
    def init(cls) -> Self:
        return cls(BiomeStatus.STARTED)

    def set_ok(self):
        self.result: BiomeStatus = BiomeStatus.OK

    def set_fail_observe(self):
        self.result: BiomeStatus = BiomeStatus.FAIL_OBSERVE

    def set_fail_create(self):
        self.result: BiomeStatus = BiomeStatus.FAIL_CREATE

    def set_created(self):
        self.result: BiomeStatus = BiomeStatus.CREATED

    def set_prompt(self):
        self.result: BiomeStatus = BiomeStatus.PROMPT
