from pathlib import Path

from .base import ArborealError, ConversationError, DataOperationError

### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### Transfer and Operation
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


# TODO: figure out if handling here or in task
class DataRuntimeError(DataOperationError, RuntimeError):
    """Handle SproutOperator(maybe->SproutError), Uploader(maybe->ApiError)"""

    def __init__(self, message=None):
        # REFACTOR:
        if message is None:
            message = "Required Data not available within this setup!"
        super().__init__(message)


class DataInputOutputError(DataOperationError, IOError):
    """Handle CampOperator, MarkdownOperator"""

    def __init__(self, message=None):
        # REFACTOR:
        if message is None:
            message = "Required Data not available in FileSystem structure!"
        super().__init__(message)


### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### Conversation
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


class PromptError(ConversationError, ValueError):  # TODO: value?
    """Track Input Parsing and Layout Creation"""

    def __init__(self, message=None):
        # REFACTOR:
        if message is None:
            message = "Problems while processing Prompt"
        super().__init__(message)


class ResponseError(ConversationError, ValueError):  # TODO: value?
    """Track Output Parsing and Statistic Management"""

    def __init__(self, message=None):
        # REFACTOR:
        if message is None:
            message = "Problems while processing Response"
        super().__init__(message)


class TreeGraphError(ConversationError):
    """Ensure Observability of all DAGs at any Time"""

    def __init__(self, message=None, bad_link=None):
        # REFACTOR:
        if bad_link:
            message = f"{bad_link} directly linked to {bad_link}"
        elif message is None:
            message = "Invalid structure in Conversation DAG"
        super().__init__(message)


### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### Arboreal
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


class ArborealDataError(ArborealError):
    """Control internal State of Biome, Forest and Tree"""

    def __init__(self, msg: str, arboreal: str, file: Path):
        # REFACTOR:
        self.arboreal = arboreal
        self.file = file
        super().__init__(msg)


# TODO: check sst.RegistrySyncError
class ArborealTrackingError(ArborealError):
    """Control Global Distributed Location of Biome, Forest and Tree"""

    def __init__(self, message=None, arbo_to_track=None):
        # REFACTOR:
        if message:
            msg: str = message
        else:
            arbo_to_track: str = arbo_to_track or "ArboT"
            msg = f"Tracker diverged from {arbo_to_track=}"
        super().__init__(msg)
