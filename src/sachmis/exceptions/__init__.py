"""
Identify unexpected problems and pinpoint what happened

Consider:
 - Data
 - Setup and Launch
 - Task

"""

__all__: list[str] = [
    "SachmisError",
    # Data
    "SachmisDataError",
    "DataOperationError",
    "DataRuntimeError",
    "DataInputOutputError",
    "ConversationError",
    "PromptError",
    "ResponseError",
    "TreeGraphError",
    "ArborealError",
    "ArborealDataError",
    "ArborealTrackingError",
    # Task
    "SachmisTaskError",
    "CapstoneError",
    "SproutError",
    "ApiCallError",
    ## model
    "DummiError",
    "GeminiError",
    "GrokError",
    # Launch
    "SachmisLaunchError",
    "NotInCampError",
]
from .base import (
    ApiCallError,
    ArborealError,
    ConversationError,
    DataOperationError,
    SachmisDataError,
    SachmisError,
    SachmisLaunchError,
    SachmisTaskError,
)
from .data import (
    ArborealDataError,
    ArborealTrackingError,
    DataInputOutputError,
    DataRuntimeError,
    PromptError,
    ResponseError,
    TreeGraphError,
)
from .launch import NotInCampError
from .task import (
    DummiError,
    GeminiError,
    GrokError,
    SproutError,
)
