import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Self

from filelock import FileLock
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from sachmis.config import SachmisConfig, get_config
from sachmis.utils.exceptions import (
    ArborealError,
    ArborealFileMissingError,
    ArborealRegistryDuplicateError,
    ArborealRegistryMissingError,
)


class Arboreal(BaseModel):
    """Common attributes of all distributed data objects"""

    unique_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_updated: datetime | None = None

    @property
    def local_created_at(self) -> str:
        """Returns a human-readable string of the creation time in the system's local timezone."""
        config: SachmisConfig = get_config()
        # TASK: time display, check -> utils, other libs (maybe arrow)
        return self.created_at.astimezone().strftime(
            config.defaults.timestamp_format
        )

    def touch(self) -> datetime:
        self.last_updated = datetime.now(UTC)
        return self.last_updated

    @property
    def n_instanciated(self) -> int:
        return self._local_counter

    _local_counter: int = 0

    @property
    def _next_instance_id(self) -> int:
        self._local_counter += 1
        self.touch()
        logger.debug(
            f"New local id {self._local_counter} created from "
            f"{self.__class__.__name__}: {self.unique_id}"
        )
        return self._local_counter

    def _attach(self, *_args, **_kwargs):
        raise NotImplementedError

    @property
    def n_children(self) -> int:
        raise NotImplementedError


class ArborealTracker(BaseModel):
    """Lightweight reference to track and write registry members,
    they are intended to be saved as their own files on disk"""

    # IDEA: merge with / derive from , SstFile

    unique_id: str
    local_id: int = 0
    path: Path
    added_at: datetime = Field(default_factory=datetime.now(UTC))

    @property
    def local_added_at(self) -> str:
        """Attribute 'added_at' in local timezone, format from config.defaults"""
        config: SachmisConfig = get_config()
        # LATER: pendulum,arrow,dateutil or sachmis|silvasta.utils
        return self.added_at.astimezone().strftime(
            config.defaults.timestamp_format
        )


class ArborealRegistry[ArboT: Arboreal](BaseModel):
    """Registry for data of Arboreals"""

    trackers: dict[str, ArborealTracker] = Field(default_factory=dict)
    _members: dict[str, ArboT] = Field(
        default_factory=dict, init=False, repr=False
    )

    @property
    def n_trackers(self) -> int:
        return len(self.trackers)

    @property
    def all_trackers(self) -> list[ArborealTracker]:
        return list(self.trackers.values())

    @property
    def n_members(self) -> int:
        return len(self._members)

    @property
    def all_members(self) -> list[ArboT]:
        return list(self._members.values())

    def find_member_or_tracker(
        self, uuid: str
    ) -> ArboT | ArborealTracker | None:
        if member := self.find_member(uuid):
            return member
        if tracker := self.find_tracker(uuid):
            return tracker
        return None

    def find_tracker(self, uuid: str) -> ArborealTracker | None:
        return self.trackers.get(uuid, None)

    def has_tracker(self, uuid: str) -> bool:
        return self.find_tracker(uuid) is not None

    def get_tracker(self, uuid: str) -> ArborealTracker:
        if not (tracker := self.find_tracker(uuid)):
            raise ArborealRegistryMissingError(
                parent=self.__class__.__name__,
                child=ArboT.__name__,
                missing_id=uuid,
            )
        return tracker

    @property
    def tracker_paths(self) -> set[Path]:
        return set(t.path for t in self.all_trackers)

    @property
    def tracker_with_invalid_paths(self) -> list[ArborealTracker]:
        return [
            tracker
            for tracker in self.all_trackers
            if not tracker.path.exists()
        ]

    def tracker_local_ids(self) -> set[int]:
        local_ids: set[int] = set(t.local_id for t in self.all_trackers)
        if len(local_ids) != self.n_trackers:
            logger.warning(f"{len(local_ids)=} but {self.n_trackers=})")
        return local_ids

    def find_tracker_by_local_id(self, id: str) -> ArborealTracker | None:
        for tracker in self.all_trackers:
            if id == tracker.local_id:
                return tracker

    def find_member(self, uuid: str) -> ArboT | None:
        return self._members.get(uuid, None)

    def has_member(self, uuid: str) -> bool:
        return self.find_member(uuid) is not None

    def get_member(self, uuid: str) -> ArboT:
        if not (member := self.find_member(uuid)):
            raise ArborealRegistryMissingError(
                parent=self.__class__.__name__,
                child=ArboT.__name__,
                missing_id=uuid,
            )
        return member

    def attach(
        self, instance: ArboT, path: Path, local_id: int
    ) -> ArborealTracker:
        """Add instance to runtime registry, create and add reference tracker to writtten registry"""
        uid: str = instance.unique_id

        # Create tracker first, in case it fails
        tracker = ArborealTracker(
            unique_id=uid,
            local_id=local_id,
            path=path,
        )
        self._members[uid] = instance
        self.trackers[uid] = tracker

        return tracker

    def confirm_not_already_added(self, unique_id: str):
        if self.has_tracker(unique_id):
            added_at: str = self.trackers[unique_id].local_added_at
            logger.error(f"uuid already in registry.references: {added_at=}")
            raise ArborealRegistryDuplicateError(
                parent=self.__class__.__name__,
                child=ArboT.__name__,
                duplicated_id=unique_id,
            )


class ArborealDisk[ArboT: Arboreal](Arboreal):
    """Common attributes of all Arboreals that are written to disk"""

    _registry: ArborealRegistry[ArboT] = Field(
        default_factory=ArborealRegistry, init=False, repr=False
    )
    # Safety toggle for save_state, otherwise needs manual lock_required
    _has_lock: bool = Field(default=False, repr=False)

    @property
    def n_children(self) -> int:
        return self._registry.n_trackers

    @classmethod
    def load_state(cls, file: Path) -> Self:
        name: str = cls.__name__
        logger.info(f"Load {name} from json")

        if not file.exists():
            logger.error(f"No {name.lower()} at target location: {file}")
            raise ArborealFileMissingError(arboreal=name, file_path=file)

        instance: Self = cls.model_validate_json(file.read_text())

        logger.info(
            f"{name} loaded with {instance.n_children} {ArboT.__name__}s"
        )
        return instance

    def save_state(self, file: Path, *, lock_required=True) -> None:
        name: str = self.__class__.__name__

        if lock_required and not self._has_lock:
            raise ArborealError(f"FileLock required to write {name}!")

        logger.info(f"Save {name} to json")
        self.touch()

        file.write_text(self.model_dump_json())

        logger.info(f"{name} saved with {self.n_children} {ArboT.__name__}s")

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
                if save_on_error:
                    instance.save_state(file)
                instance._has_lock = False  # probably redundant
                logger.debug(f"--- Lock released for {name} ---")

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

    def _attach(
        self, instance: ArboT, path: Path, local_id: int | None = None
    ) -> ArborealTracker:
        """Add instance to runtime registry, create and add reference tracker to writtten registry"""

        self._registry.confirm_not_already_added(instance.unique_id)

        tracker: ArborealTracker = self._registry.attach(
            instance, path, local_id or self._next_instance_id
        )
        logger.debug(
            f"Attached {ArboT.__name__} {local_id} to {self.__class__.__name__}"
        )
        return tracker

    def _check_tracker_paths_exist(self) -> bool:
        """Detect tracker with missing files at path"""
        if missing_paths := self._registry.tracker_with_invalid_paths:
            missing: str = "\n".join(str(p) for p in missing_paths)
            logger.warning(f"Missing {ArboT.__name__} files:\n{missing}")
            return False
        return True

    def _check_tracker_paths_unique(self) -> bool:
        """Detect tracker with missing files at path"""
        paths: set[Path] = self._registry.tracker_paths
        if (n_unique_paths := len(paths)) != self.n_children:
            logger.warning(f"{n_unique_paths=} but {self.n_children=})")
            return False
        return True
