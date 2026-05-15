import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Self

from filelock import FileLock
from loguru import logger
from pydantic import BaseModel, Field, PrivateAttr, ValidationError
from sstcore.data import SstFile

from ...config import SachmisConfig, get_config
from ...exceptions import (
    ArborealError,
    ArborealFileMissingError,
    ArborealRegistryDuplicateError,
    ArborealRegistryMissingError,
)


class ArborealTracker[ArboT: Arboreal](SstFile):
    """Lightweight reference to track and write registry members"""

    unique_id: str
    local_id: int = 0

    @classmethod
    def sample(cls, arbo: ArboT, path: Path, local_id: int) -> ArborealTracker:
        """Sample Tracker From Arboreal"""
        # NEXT: check how to use path, as well in B,F,T
        return ArborealTracker(
            unique_id=arbo.unique_id,
            local_id=local_id,
            local_path=path,
        )


class ArborealRegistry[ArboT: Arboreal](BaseModel):
    """Registry for data of Arboreals"""

    trackers: dict[str, ArborealTracker] = Field(default_factory=dict)
    # LATER: Generalize with sstcore.FileRegistry

    @property
    def n_trackers(self) -> int:
        return len(self.trackers)

    @property
    def all_trackers(self) -> list[ArborealTracker]:
        return list(self.trackers.values())

    def find_tracker(self, uuid: str) -> ArborealTracker | None:
        return self.trackers.get(uuid, None)

    def has_tracker(self, uuid: str) -> bool:
        return self.find_tracker(uuid) is not None

    def get_tracker(self, uuid: str) -> ArborealTracker:
        if not (tracker := self.find_tracker(uuid)):
            # LATER: def raise_missing? prefilled text?
            raise ArborealRegistryMissingError(
                parent=self.__class__.__name__,
                child=ArboT.__name__,
                missing_id=uuid,
            )
        return tracker

    @property
    def tracker_paths(self) -> set[Path]:
        return set(t.local_path for t in self.all_trackers)

    def tracker_with_invalid_paths(self) -> list[ArborealTracker]:
        return [
            tracker
            for tracker in self.all_trackers
            if not tracker.local_path.exists()  # TODO: local_path? local_dir?
        ]

    def tracker_local_ids(self) -> set[int]:
        local_ids: set[int] = set(t.local_id for t in self.all_trackers)
        if len(local_ids) != self.n_trackers:
            logger.warning(f"{len(local_ids)=} but {self.n_trackers=})")
        return local_ids

    def find_tracker_by_local_id(self, id: int) -> ArborealTracker | None:
        for tracker in self.all_trackers:
            if id == tracker.local_id:
                return tracker

    def attach(
        self, arbo: ArboT, path: Path, local_id: int
    ) -> ArborealTracker:
        """Sample Tracker from Arboreal and attach to registry"""
        tracker: ArborealTracker = arbo.sample_tracker(
            local_id=local_id, path=path
        )
        return self.add(tracker)

    def add(self, tracker: ArborealTracker) -> ArborealTracker:
        self._confirm(tracker)
        self.trackers[tracker.unique_id] = tracker
        logger.info(
            f"Attached {ArboT.__name__} {tracker.local_id} to {self.__class__.__name__}"
        )
        return tracker

    def _confirm(self, tracker: ArborealTracker):
        """Collection of all checks"""
        self._ensure_not_already_added(tracker.unique_id)
        self._ensure_path(tracker)

    def _ensure_not_already_added(self, unique_id: str):
        """Check if tracker uuid not in Registry"""
        if self.has_tracker(unique_id):
            added_at: str = self.trackers[unique_id].added_at
            logger.error(f"uuid already in registry.references: {added_at=}")
            raise ArborealRegistryDuplicateError(
                parent=self.__class__.__name__,
                child=ArboT.__name__,
                duplicated_id=unique_id,
            )

    def _ensure_path(self, tracker: ArborealTracker):
        """Check if tracker path valid"""
        if not tracker.local_path.exists():
            path: Path = tracker.local_path
            logger.error(f"Attempt to add new Tracker with invalid {path=}")
            raise ArborealRegistryMissingError(
                parent=self.__class__.__name__,
                child=ArboT.__name__,
                missing_id=tracker.unique_id,
            )

    def check_tracker_paths_exist(self) -> bool:
        """Check Registry for tracker with duplicated paths"""
        if missing_paths := self.tracker_with_invalid_paths():
            missing: str = "\n".join(str(p) for p in missing_paths)
            logger.warning(f"Missing {ArboT.__name__} files:\n{missing}")
            return False
        return True

    # LATER: prune missing?

    def check_tracker_paths_unique(self) -> bool:
        """Check Registry for tracker with duplicated paths"""
        paths: set[Path] = self.tracker_paths
        if (n_unique_paths := len(paths)) != self.n_trackers:
            logger.warning(f"{n_unique_paths=} but {self.n_trackers=})")
            return False
        return True


class Arboreal[ArboT: Arboreal](BaseModel):
    """Common attributes of all distributed data objects"""

    unique_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    local_counter: int = 0

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_updated: datetime | None = None

    # Safety toggle, set this or save_state(lock_required=True)
    _has_lock: bool = PrivateAttr(default=False)

    # REMOVE: for Tree? New derived class? Ignore?
    registry: ArborealRegistry[ArboT] = Field(
        default_factory=ArborealRegistry, init=False, repr=False
    )

    def touch(self) -> datetime:
        self.last_updated: datetime = datetime.now(UTC)
        return self.last_updated

    @property
    def stat(self):
        """Short representation for printable statistics"""
        return f"{self.__class__.__name__}: {self.local_created_at}"

    @property
    def local_created_at(self) -> str:
        """Returns a human-readable string of the creation time in the system's local timezone."""
        config: SachmisConfig = get_config()
        # LATER: time display, check -> utils, other libs (maybe arrow)
        return self.created_at.astimezone().strftime(
            config.defaults.timestamp_format
        )

    def sample_tracker(self, path: Path, local_id: int) -> ArborealTracker:
        """Sample Tracker from Self Arboreal (not from registry)"""
        # NEXT: check how to use path, as well in B,F,T
        return ArborealTracker(
            unique_id=self.unique_id,
            local_id=local_id,
            local_path=path,
        )

    @property
    def child_info(self):  # TODO: improve, override in subclass!
        """Used for Biome and Forest, override for Tree!"""
        return f"{self.registry.n_trackers} {ArboT.__name__}"

    def _next_instance_id(self) -> int:
        self.local_counter += 1
        self.touch()
        logger.debug(
            f"New local id {self.local_counter} created from "
            f"{self.__class__.__name__}: {self.unique_id}"
        )
        return self.local_counter

    @classmethod
    def read_mode(cls, file: Path) -> Self:
        """Check for half-written file of other process by pydantic validation"""

        # PARAM: -> defaults
        n_retry: int = 3
        delay: float = 0.1  # seconds

        name: str = cls.__name__
        logger.debug(f"Loading {name} without lock")

        for attempt in range(n_retry):
            try:
                instance: Self = cls.load_state(file)
                return instance
            except ValidationError as e:
                if e.errors()[0].get("type") == "json_invalid":
                    logger.debug(f"JSON invalid/half-written. {attempt=}.")
                    time.sleep(delay)
                else:
                    logger.error(f"Schema validation failed for {file=}")
                    raise

        raise RuntimeError(f"JSON unreadable (likely corrupted) {file=}")

    @classmethod
    @contextmanager
    def edit_mode(cls, file: Path, save_on_error=False) -> Iterator[Self]:
        """Provide the loaded object locked in filesystem while editing"""

        # PARAM: -> defaults
        timeout: int = 60  # seconds

        name: str = cls.__name__
        lock_file: Path = file.with_suffix(file.suffix + ".lock")

        with FileLock(lock_file, timeout=timeout):
            logger.debug(f"--- Lock acquired for {name} ---")

            instance: Self = cls.load_state(file)
            instance._has_lock = True
            try:
                yield instance
                instance.save_state(file)

            # LATER: define which Exceptions raise, which allow write or not

            finally:
                if save_on_error:  # IDEA: save to backup file?
                    instance.save_state(file)
                instance._has_lock = False  # probably redundant
                logger.debug(f"--- Lock released for {name} ---")

    @classmethod
    def load_state(cls, file: Path) -> Self:
        name: str = cls.__name__
        logger.info(f"Load {name} from json")

        if not file.exists():
            logger.error(f"No {name.lower()} at target location: {file}")
            raise ArborealFileMissingError(arboreal=name, file=file)

        instance: Self = cls.model_validate_json(file.read_text())

        logger.info(f"{name} loaded with {instance.child_info}s")
        return instance

    def save_state(self, file: Path, *, lock_required=True) -> None:
        logger.info(f"Save {(arbo := self.__class__.__name__)} to json")

        if lock_required and not self._has_lock:
            raise ArborealError(f"FileLock required to write {arbo}!")

        self.touch()
        file.write_text(self.model_dump_json())

        logger.info(f"{arbo} saved with {self.child_info}")
