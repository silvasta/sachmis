# TASK:
# - Data
#   - Check structured response
# - Thunder and Fire structure


from importlib.metadata import PackageNotFoundError, version

try:  # Show pyproject.toml package name
    __version__: str = version("sachmis")
except PackageNotFoundError:
    __version__ = "unknown"

# NOTE: logging?

__all__: list = []
