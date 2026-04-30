from pathlib import Path

from .base import ArborealError


class ArborealFileMissingError(FileNotFoundError, ArborealError):
    """Raised when an Arboreal file (for now, JSON) is missing"""

    def __init__(self, arboreal: str, file: Path):
        msg = f"No {arboreal} found at target location: {file}"
        super().__init__(msg)


class ArborealFileExistsError(FileExistsError, ArborealError):
    """Raised when trying to create an Arboreal file that already exists"""

    def __init__(self, arboreal: str, file: Path):
        msg = f"Found existing {arboreal} at target location: {file}"
        super().__init__(msg)


class ArborealRegistryMissingError(KeyError, ArborealError):
    """Raised when an ID is not found in an object's internal registry"""

    def __init__(self, parent: str, child: str, missing_id: str):
        msg = f"{parent} registry has no {child} with: {missing_id=}"
        super().__init__(msg)


class ArborealRegistryDuplicateError(KeyError, ArborealError):
    """Raised when an ID is already attached in an Arboreals internal registry"""

    def __init__(self, parent: str, child: str, duplicated_id: str):
        msg = f"{parent} registry already has {child} with: {duplicated_id=}"
        super().__init__(msg)


class SproutResponseExistsError(AttributeError, ArborealError):
    """Response already exists in Sprout runtime data"""

    # MOVE: SachmisDataError?
    def __init__(self, unique_id: str):
        msg = f"Cannot override existing response for Sprout: {unique_id=}"
        super().__init__(msg)


class SproutResponseMissingError(KeyError, ArborealError):
    """Response in already 'growed' Sprout missing"""

    # MOVE: SachmisDataError?
    def __init__(self, unique_id: str):
        msg = f"Cannot find expected response for Sprout: {unique_id=}"
        super().__init__(msg)


class SproutRegistryError(ValueError, ArborealError):
    """Problem with sub-Sprouts, invalid keys etc."""
