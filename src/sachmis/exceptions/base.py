class SachmisError(Exception):
    """Root of all custom project Exceptions"""


class ArborealError(SachmisError):
    # NEXT: check and confirm
    """Root of all Arboreal Errors"""


class SachmisLaunchError(SachmisError):
    # NEXT: check and confirm
    # TODO: other launch issues?
    """CLI launched from invalid filesystem location"""


class SachmisDataError(SachmisError):
    # NEXT: as root for data manager
    """Problems with internal data structure"""
