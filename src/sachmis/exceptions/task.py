from .base import ApiCallError, SachmisTaskError

### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### Capstone
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


class CapstoneError(SachmisTaskError):  # IMPORTANT:
    """Observe the Main Routing Point of the Project"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### Internal Data Connection
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


# NOTE: check potential overlap with .data.DataOperationError
class SproutError(SachmisTaskError):  # TASK:
    """Track Position of Global Data Connector"""


# IDEA: Handler that go down together with DataManager?


### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### API
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


class GrokError(ApiCallError):
    """Attach Model specific information to hook"""

    def __init__(self, *args, **kwargs):
        # TODO:
        super().__init__(*args, **kwargs)


class GeminiError(ApiCallError):
    """Attach Model specific information to hook"""

    def __init__(self, *args, **kwargs):
        # TODO:
        super().__init__(*args, **kwargs)


class DummiError(ApiCallError):
    """Attach at least 1 Funny Statistic"""

    def __init__(self, *args, **kwargs):
        # TODO:
        super().__init__(*args, **kwargs)
