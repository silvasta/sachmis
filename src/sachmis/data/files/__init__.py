"""
Handle FileSystem Input and Output

- Combine FileTracker and FileRegistry

"""

__all__: list[str] = [
    "MarkdownRegistry",
    "RoleRegistry",
    "Role",
    "UploadFile",
]

from .markdown import MarkdownRegistry
from .role import Role, RoleRegistry
from .upload import UploadFile
