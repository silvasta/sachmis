"""
Operators - The guys who actually care about the jobs assigned to data

"""

__all__: list[str] = [
    "MarkdownOperator",
    "SproutOperator",
    "CampManager",
]

from .markdown import MarkdownOperator
from .oasis import CampManager
from .sprout import SproutOperator
