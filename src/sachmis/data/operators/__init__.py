"""
Operators - The guys who actually care about the jobs assigned to data
"""

__all__: list[str] = [
    "FrontFileHandler",
    "DataHandler",
]
from .front import FrontFileHandler
from .runtime import DataHandler


# NEXT:
# NEXT:
# NEXT:
class MarkdownOperator:
    """Scan Filesystem, load Prompt, write Response, if needed in new Folder"""


# NEXT:
# NEXT:
# NEXT:
# NEXT:
class SproutOperator:
    """Extract DAG from Tree and provide Agents with Prompt and get Response"""
