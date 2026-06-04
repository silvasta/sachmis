from .base import SachmisLaunchError


class NotInForestError(FileNotFoundError, SachmisLaunchError):
    """Current Task needs CWD inside base_dir with Forest"""

    def __init__(self, message=None):
        if message is None:
            super().__init__(_message_not_in("Base with Forest"))
        else:
            super().__init__(message)


class NotInCampError(FileNotFoundError, SachmisLaunchError):
    """Current Task needs CWD inside camp_dir"""

    def __init__(self, message=None):
        if message is None:
            super().__init__(_message_not_in("Camp of Forest and Base"))
        else:
            super().__init__(message)


# MOVE: to error handling in app
def _message_not_in(identifier) -> str:
    return (
        f"\nCurrent location not in {identifier}!"
        # IMPORTANT: sync with newest updates in CLI
        "\nCreate new Base with Forest: sachmis init {-n NAME}"
        "\nFind existing Bases with: sachmis show bases"
    )
