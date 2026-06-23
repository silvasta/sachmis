from .base import SachmisLaunchError

# IDEA:s config, cli(after launch), ....


class NotInCampError(FileNotFoundError, SachmisLaunchError):
    """Launch needs CWD inside IretCamp with Forest and sOasis"""

    def __init__(
        self,
        # IDEA: this in root? with always forward, sometimes use?
        message=None,
    ):
        if message is None:
            super().__init__(_message_not_in("Camp of Forest and Base"))
        else:
            super().__init__(message)


# REFACTOR: to error handling in app
def _message_not_in(identifier) -> str:
    return (
        f"\nCurrent location not in {identifier}!"
        # IMPORTANT: sync with newest updates in CLI
        "\nCreate new Base with Forest: sachmis init {-n NAME}"
        "\nFind existing Bases with: sachmis show bases"
    )
