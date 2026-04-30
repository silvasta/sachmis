class SachmisError(Exception):
    """Root of all custom project Exceptions"""


class ArborealError(SachmisError):
    """Root of all Arboreal Errors"""


class SachmisLaunchError(SachmisError):
    # TODO: other launch issues?
    """CLI launched from invalid filesystem location"""


class SachmisDataError(SachmisError):
    """Problems with internal data structure"""
