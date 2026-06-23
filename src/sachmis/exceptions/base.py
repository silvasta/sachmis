from sstcore.exceptions import SstError


class SachmisError(SstError):
    """Root of all Custom Project Errors"""


### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### DataError
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


class SachmisDataError(SachmisError):
    # TODO: check if and what to attach, maybe just bundle catcher
    """Root of all Data Level Errors"""


### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


class DataOperationError(SachmisDataError):
    """Track Data from FileSystem trough Pipeline and Back"""


class ArborealError(SachmisDataError):
    """Observe interaction of Arboreals and Distributed Files"""


class ConversationError(SachmisDataError):
    """Observe interaction of Promp, Response, and Graph"""


### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### TaskError
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


class SachmisTaskError(SachmisError):
    # TODO: check if and what to attach, maybe just bundle catcher
    """Observe Status of Task Execution"""


### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


class ApiCallError(SachmisTaskError):  # TASK:
    """Gather all information, ID, Time, Retry..."""


### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### LaunchError (maybe SettingError,Setuperror)
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


class SachmisLaunchError(SachmisError):
    # TODO: check if and what to attach, maybe just bundle catcher
    """Observe Problems that happens before and around Execution"""
