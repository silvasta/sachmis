from .base import SachmisDataError


class PromptError(ValueError, SachmisDataError):
    # TASK: this as SachmisLaunchError??? check with response
    def __init__(self, message=None):
        if message is None:
            message = "Problems while processing Prompt"
        super().__init__(message)


class ResponseError(ValueError, SachmisDataError):
    # TASK: this as Data/Sprout?
    def __init__(self, message=None):
        if message is None:
            message = "Problems while processing Prompt"
        super().__init__(message)


class ConversationGraphError(AttributeError, SachmisDataError):
    # TASK: this as Sprout?
    """Intended for Bipartite DAG failures"""

    def __init__(self, message=None, bad_link=None):
        if bad_link:
            message = f"{bad_link} directly linked to {bad_link}"
        elif message is None:
            message = "Invalid structure in Conversation DAG"
        super().__init__(message)


class PromptRegistryError(ConversationGraphError):
    # TASK: this as Sprout?
    def __init__(self, message=None):
        if message is None:
            message = "Invalid structure in Conversation DAG"
        super().__init__(message)


class ResponseRegistryError(ConversationGraphError):
    # TASK: this as Sprout?
    def __init__(self, message=None):
        if message is None:
            message = "Invalid structure in Conversation DAG"
        super().__init__(message)


class DataRuntimeError(RuntimeError, SachmisDataError):
    def __init__(self, message=None):
        # TASK: this as base for DataManager
        if message is None:
            message = "Required Data not available within this setup!"
        super().__init__(message)


class DataRolloutError(RuntimeError, SachmisDataError):
    # TASK: this as base for DataManager
    def __init__(self, message=None):
        if message is None:
            message = "Required Data not available in FileSystem structure!"
        super().__init__(message)
