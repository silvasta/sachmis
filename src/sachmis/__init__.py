#  TASK: for v0.4.0
# - Extended Forest Rollout
# - Arboreal as SimpleTree
# - Structured response
# - Hardlink Registry
# - Files Interface
# - Image Loading
# - Thunder

from importlib.metadata import PackageNotFoundError, version

try:  # Show pyproject.toml package name
    __version__: str = version("sachmis")
except PackageNotFoundError:
    __version__ = "unknown"

__all__: list[str] = []
