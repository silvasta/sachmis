"""
Identify unexpected problems and pinpoint what happened

Consider:
 - Data
 - Setup and Launch
 - Task
"""

# FIX: Message from Trouble: why?
#    ~/PolyBox/Code/sachmis/latest/src/sachmis/exceptions/  7
#   └╴󰌠  __init__.py  7
#     ├╴  `.base.ApiCallError` imported but unused; consider removing, adding to `__all__`, or using a redundant alias Ruff (F401) [38, 5]
#     ├╴  `.base.SachmisLaunchError` imported but unused; consider removing, adding to `__all__`, or using a redundant alias Ruff (F401) [44, 5]
#     ├╴  `.base.SachmisTaskError` imported but unused; consider removing, adding to `__all__`, or using a redundant alias Ruff (F401) [45, 5]
#     ├╴  `.task.DummiError` imported but unused; consider removing, adding to `__all__`, or using a redundant alias Ruff (F401) [58, 5]
#     ├╴  `.task.GeminiError` imported but unused; consider removing, adding to `__all__`, or using a redundant alias Ruff (F401) [59, 5]
#     ├╴  `.task.GrokError` imported but unused; consider removing, adding to `__all__`, or using a redundant alias Ruff (F401) [60, 5]
#     └╴  `.task.SproutError` imported but unused; consider removing, adding to `__all__`, or using a redundant alias Ruff (F401) [61, 5]

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
