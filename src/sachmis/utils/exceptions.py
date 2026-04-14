from pathlib import Path


class SachmisError(Exception):
    """Root of all custom project Exceptions"""


class ArborealError(SachmisError):
    """Root of all Arboreal Errors"""


class ArborealFileMissingError(FileNotFoundError, ArborealError):
    """Raised when an Arboreal (JSON) file is missing"""  # TODO: JSON?

    def __init__(self, arboreal: str, file_path: Path):
        super().__init__(
            f"No {arboreal} found at target location: {file_path}"
        )


class ArborealFileExistsError(FileExistsError, ArborealError):
    """Raised when trying to create an Arboreal file that already exists"""

    def __init__(self, arboreal: str, file_path: Path):
        super().__init__(
            f"Found existing {arboreal} at target location: {file_path}"
        )


class ArborealRegistryMissingError(KeyError, ArborealError):
    """Raised when an ID is not found in an object's internal registry"""

    def __init__(self, parent: str, child: str, missing_id: str):
        super().__init__(
            f"{parent} registry has no {child} with: {missing_id=}"
        )


class ArborealRegistryDuplicateError(KeyError, ArborealError):
    """Raised when an ID is already attached in an Arboreals internal registry"""

    def __init__(self, parent: str, child: str, duplicated_id: str):
        super().__init__(
            f"{parent} registry already has {child} with: {duplicated_id=}"
        )


class SproutResponseExistsError(AttributeError, ArborealError):
    """Response already exists in Sprout runtime data"""

    def __init__(self, unique_id: str):
        super().__init__(
            f"Cannot override existing response for Sprout {unique_id}."
        )


class SproutRegistryError(ValueError, ArborealError):
    """Response already exists in Sprout runtime data"""

    def __init__(self, unique_id: str):
        super().__init__(
            f"Cannot override existing response for Sprout {unique_id}."
        )


# TODO: SproutResponseMissingError ??


class NotInForestError(FileNotFoundError, SachmisError):
    """Raised when CWD not inside proper filesystem structure for desired task"""

    def __init__(self, message=None):
        if message is None:
            message = (
                "Current location not in Base with Forest!"
                "Create new Base with Forest: sachmis init {-n NAME}"
                "Find existing Bases with: sachmis show bases"
            )
        super().__init__(message)
