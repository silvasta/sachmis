from pathlib import Path
from typing import Literal

from sstcore.utils import ColorBox

from .base import ArborealError, ConversationError, DataOperationError

### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### Transfer and Operation
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --

c: ColorBox = ColorBox.bold()


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

    def __init__(
        self,
        issue: str,
        arbo: str = "Arboreal",
    ):
        super().__init__()
        self.issue: str = issue
        self.arbo: str = arbo


class ArborealTrackingError(ArborealError):
    """Control Global Distributed Location of Biome, Forest and Tree"""

    def __init__(
        self,
        file: Path,
        issue: Literal["Missing", "Exists"],
        arbo: str = "Arboreal",
    ):
        super().__init__(file=str(file), issue=issue, arbo=arbo)
        self.file: Path = file
        self.issue: str = issue
        self.arbo: str = arbo

    def _modify_if_needed(self, rows: list[str]) -> None:
        rows.append(f"{c.g(self.arbo + 'File')}{c.r(self.issue)}")
        rows.append(str(self.file))  # LATER: colorize?
