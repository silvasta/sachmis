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
from sstcore.utils.print import ColorBox

from ...config import SachmisConfig, get_config
from ...exceptions import (
    ArborealError,
    ArborealFileMissingError,
    ArborealRegistryDuplicateError,
    ArborealRegistryMissingError,
    DataRuntimeError,
)
from ...exceptions.arbo import ArborealTrackerError

c = ColorBox()


class ArboView:  # LATER: check similar for SstFile
    """Mixin for clean Representation of Arboreals"""

    def _get_local_id(self) -> int | None:
        if hasattr(self, "tracker") and hasattr(self.tracker, "local_id"):
            return getattr(self.tracker, "local_id", None)

    @property
    def cli(self) -> str:
        """Custom colorized short label for CLI headers and explicit UI prints."""
        name: str = self.__class__.__name__
        local_id: int = self._get_local_id() or -1
        return c.white(f"{c.green(name)}[{c.blue(local_id)}]")

    @property
    def time_stat(self) -> str:
        """Colorized statistic for printer"""
        return f"{self.cli}: created at {self.local_created_at}"

    @property
    def local_created_at(self) -> str:
        """System local timezone creation string"""
        if not (created_at := getattr(self, "created_at", None)):
            return "N/A"
        config: SachmisConfig = get_config()
        # LATER: printer dispatch for custom datetime prints
        return created_at.astimezone().strftime(
            config.defaults.timestamp_format
        )

    def __str__(self) -> str:
        """Short readable summary. No colors. Safe for logging."""
        cls_name = self.__class__.__name__
        if (local_id := self._get_local_id()) is not None:
            return f"{cls_name}(local_id={local_id})"
        return cls_name

    def __repr__(self) -> str:
        """Detailed plain-text representation for debugging and {obj=}"""
        cls_name: str = self.__class__.__name__
        local_id: int | str = self._get_local_id() or "N/A"
        uid: str = getattr(self, "unique_id", "No-UUID")[:8]
        child_str = (
            f", children={self.child_info}"
            if hasattr(self, "child_info")
            else ""
        )
        return f"<{cls_name} id={local_id} uuid={uid}...{child_str}>"


class ArborealTracker[ArboT: Arboreal](SstFile):  # LATER: ArboT?
    """Lightweight reference to track and write registry members"""

    arbo_t: str
    path: Path

    unique_id: str
    local_id: int = 0

    @property
    def stem(self):
        return self.path.stem

    @property
    def has_valid_path(self) -> bool:
        if not (path := self.path).is_file():
            logger.warning(f"No {self.arbo_t} File found at: {path=}")
            return False
        return True

    @classmethod
    def setup(
        cls, arbo_t: str, path: Path, unique_id: str, local_id: int
    ) -> Self:
        logger.warning(f"what is {arbo_t=}")  # REMOVE:
        tracker: ArborealTracker = cls(
            unique_id=unique_id,
            local_id=local_id,
            path=path,
            local_path=path,
            arbo_t=arbo_t,
        )
        if tracker.has_valid_path:
            return tracker
        else:
            raise ArborealFileMissingError(arboreal=arbo_t, file=path)


class ArborealRegistry[ArboT: Arboreal](BaseModel):
    """Registry for data of Arboreals"""

    # FIX: ArboT.__name__ fails...

    trackers: dict[str, ArborealTracker] = Field(default_factory=dict)

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
            raise ArborealRegistryMissingError(
                parent=self.__class__.__name__,
                child=ArboT.__name__,  # TEST: does this work? no...
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
            if not tracker.local_path.exists()
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
        self, arboreal: ArboT, path: Path, local_id: int
    ) -> ArborealTracker:
        """Sample Tracker from Arboreal and attach to registry"""
        tracker: ArborealTracker = arboreal.sample_tracker(
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


class Arboreal[ArboT: Arboreal](ArboView, BaseModel):
    """Common attributes of all distributed data objects"""

    tracker: ArborealTracker
    unique_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    local_counter: int = 0

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_updated: datetime | None = None

    # Safety toggle, set this or save_state(lock_required=True)
    _has_lock: bool = PrivateAttr(default=False)

    # REMOVE: for Tree? New derived class? Ignore? create Mixin of Registry?
    registry: ArborealRegistry[ArboT] = Field(
        default_factory=ArborealRegistry, init=False, repr=False
    )

    def touch(self) -> datetime:
        self.last_updated: datetime = datetime.now(UTC)
        return self.last_updated

    def sample_tracker(
        self, path: Path, local_id: int = 0, strict=True
    ) -> ArborealTracker:
        """Sample Tracker from Self.Arboreal (not from registry)"""

        if not path.exists():
            if strict:
                raise ArborealFileMissingError(self.__class__.__name__, path)
            logger.error(f"Tracker sampling with invalid {path=}")

        # LATER: resolve errors somehow else, are failures even expected?
        # - create log setup to track and catch this
        match (id := self.tracker.local_id, local_id):
            case (0, 0):
                raise DataRuntimeError("Invalid ID: tracked_id = 0 = local_id")
            case (0, _):
                logger.warning(f"Use {local_id=} instead of tracker_{id=}")
                id: int = local_id
            case (_, 0):
                logger.info(f"Using existing tracker_{id=}")
            case (_, _):
                if id == local_id:
                    logger.info(f"Using confirmed_{id=}")
                else:
                    logger.warning(f"Use {local_id=} instead of tracked:{id=}")
                    id: int = local_id

        logger.debug(f"{self}: {self.unique_id}")

        return ArborealTracker.setup(
            local_id=id,
            path=path,
            unique_id=self.unique_id,
            arbo_t=self.__class__.__name__,  # TODO: replace somehow
            # IDEA: use Arboreal instance as input?
            # - modify tracker cls method or create second
            # - Tracker should only copy name/id/path attributes!
        )

    @classmethod
    def create_with_tracker(cls, path: Path, local_id: int, **kwargs) -> Self:
        """Prefill Tracker before init, update UUID afterwards"""

        # LATER: move to debug or change log completely
        logger.info(f"Create {cls.__name__} {local_id}: tracker without uuid")

        tracker: ArborealTracker[Self] = ArborealTracker(
            local_id=local_id,
            path=path,
            unique_id="",
            arbo_t=cls.__name__,
            local_path=path,
        )
        instance: Self = cls(tracker=tracker, **kwargs)

        instance.tracker.unique_id = instance.unique_id
        instance._ensure_tracker(path)
        logger.info(f"uuid attached: {instance}")

        return instance

    @property
    def child_info(self):
        """Used for Biome and Forest, override for Tree!"""
        # FIX: ArboT fails...
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

        n_retry: int = 3  # PARAM: -> defaults
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

    def _ensure_tracker(self, path):
        if self._tracker_adapted(path):
            if self._tracker_adapted(path):
                logger.error("Tracker not ensured after 2 attempts")

    def _tracker_adapted(self, path: Path):
        # LATER: local_id from upper instance??
        tracker: ArborealTracker = self.tracker
        updated = False

        if tracker.arbo_t != self.__class__.__name__:
            logger.error(
                f"updating {tracker.arbo_t=} for {self.__class__.__name__}"
            )
            tracker.arbo_t = self.__class__.__name__
            updated = True

        if tracker.unique_id != self.unique_id:
            logger.error(f"UUID!\n{tracker.unique_id=}\n{self.unique_id=}")
            raise ArborealTrackerError(arbo_to_track=self.__class__.__name__)

        if tracker.path != path:
            logger.warning(f"updating {tracker.path=} to {path=}")
            tracker.path = path
            updated = True

        return updated

    def save_state(self, file: Path, *, lock_required=True) -> None:
        logger.info(f"Save {(arbo := self.__class__.__name__)} to json")

        if lock_required and not self._has_lock:
            raise ArborealError(f"FileLock required to write {arbo}!")

        self._ensure_tracker(path=file)
        self.touch()
        file.write_text(self.model_dump_json(indent=2))

        logger.info(f"{arbo} saved with {self.child_info}")
