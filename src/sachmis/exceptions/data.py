from .base import SachmisDataError


class PromptError(ValueError, SachmisDataError):  # TEST: ValueError?
    def __init__(self, message=None):
        if message is None:
            message = "Problems while processing Prompt"
        super().__init__(message)

