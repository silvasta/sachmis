from pathlib import Path

from .base import ArborealError


# exceptions/arbo.py
class ArborealFileError(ArborealError):
    def __init__(self, msg: str, arboreal: str, file: Path):
        self.arboreal = arboreal
        self.file = file
        super().__init__(msg)


class ArborealFileMissingError(ArborealFileError, FileNotFoundError):
    def __init__(self, arboreal: str, file: Path):
        msg = f"No {arboreal} found at target location: {file}"
        ArborealFileError.__init__(self, msg, arboreal, file)


class ArborealFileExistsError(ArborealFileError, FileExistsError):
    def __init__(self, arboreal: str, file: Path):
        msg = f"Found existing {arboreal} at target location: {file}"
        ArborealFileError.__init__(self, msg, arboreal, file)


class ArborealRegistryError(ArborealError):
    """Specific for Registry Files"""


class ArborealRegistryMissingError(KeyError, ArborealRegistryError):
    """Raised when an ID is not found in an object's internal registry"""

    def __init__(self, parent: str, child: str, missing_id: str):
        self.missing_id = missing_id
        msg = f"{parent} registry has no {child} with: {missing_id=}"
        super().__init__(msg)


class ArborealRegistryDuplicateError(KeyError, ArborealRegistryError):
    """Raised when an ID is already attached in an Arboreals internal registry"""

    def __init__(self, parent: str, child: str, duplicated_id: str):
        self.missing_id = duplicated_id
        msg = f"{parent} registry already has {child} with: {duplicated_id=}"
        super().__init__(msg)


class ArborealTrackerError(AttributeError, ArborealError):
    """For lightweight Arboreal Tracker Files"""

    def __init__(self, message=None, arbo_to_track=None):
        if message:
            msg: str = message
        else:
            arbo_to_track: str = arbo_to_track or "ArboT"
            msg = f"Tracker diverged from {arbo_to_track=}"
        super().__init__(msg)
