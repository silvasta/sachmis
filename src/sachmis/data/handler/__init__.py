"""
DataHandler - The guys who actually care about the jobs assigned to data
"""

__all__: list[str] = [
    "FrontFileHandler",
    "DataHandler",
]
from .front import FrontFileHandler
from .runtime import DataHandler
