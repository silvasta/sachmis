from .base import SachmisDataError


class PromptError(ValueError, SachmisDataError):
    def __init__(self, message=None):
        if message is None:
            message = "Problems while processing Prompt"
        super().__init__(message)


class ResponseError(ValueError, SachmisDataError):
    def __init__(self, message=None):
        if message is None:
            message = "Problems while processing Prompt"
        super().__init__(message)


class ConversationGraphError(AttributeError, SachmisDataError):
    """Intended for Bipartite DAG failures"""

    def __init__(self, message=None, bad_link=None):
        if bad_link:
            message = f"{bad_link} directly linked to {bad_link}"
        elif message is None:
            message = "Invalid structure in Conversation DAG"
        super().__init__(message)


class PromptRegistryError(ConversationGraphError):
    def __init__(self, message=None):
        if message is None:
            message = "Invalid structure in Conversation DAG"
        super().__init__(message)


class ResponseRegistryError(ConversationGraphError):
    def __init__(self, message=None):
        if message is None:
            message = "Invalid structure in Conversation DAG"
        super().__init__(message)


class DataRuntimeError(RuntimeError, SachmisDataError):
    def __init__(self, message=None):
        if message is None:
            message = "Required Data not available within this setup!"
        super().__init__(message)


class DataRolloutError(RuntimeError, SachmisDataError):
    def __init__(self, message=None):
        if message is None:
            message = "Required Data not available in FileSystem structure!"
        super().__init__(message)
