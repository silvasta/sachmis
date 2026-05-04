# TASK:
# - Forest Rollout
# - Tree and Sprout Selection
# - Hardlink Registry
# - Check structured response
# - Thunder and fire structure
# - Files Interface


from importlib.metadata import PackageNotFoundError, version

try:  # Show pyproject.toml package name
    __version__: str = version("sachmis")
except PackageNotFoundError:
    __version__ = "unknown"

__all__: list[str] = []
