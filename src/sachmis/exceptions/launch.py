from .base import SachmisLaunchError


class NotInCampError(SachmisLaunchError, FileNotFoundError):
    """Launch needs CWD inside IretCamp with Forest and Oasis"""

    def __init__(self, message=None):
        # NOTE: that made more sense when multiple used this...
        message: str = message or _assemble(location="Camp of Forest and Base")
        super().__init__(message)


def _assemble(location) -> str:
    return (  # REFACTOR: to error handling in app
        f"\nCurrent location not in {location}!"
        # IMPORTANT: sync with newest updates in CLI
        "\nCreate new Base with Forest: sachmis init {-n NAME}"
        "\nFind existing Bases with: sachmis show bases"
    )
