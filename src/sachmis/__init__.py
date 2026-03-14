# NEXT:
# - Data improvement
#   - forest handling
# - Forest
#   - save response as json
#     - transform from-to file
#   - file roleout or not
# - Check structured response
# - Thunder and Fire structure
# - base script with all functionalities for thunder


# TASK: later
# - usage
# - image creation
# - tui

from importlib.metadata import PackageNotFoundError, version

try:  # Show pyproject.toml package name
    __version__: str = version("sachmis")
except PackageNotFoundError:
    __version__ = "unknown"

# NOTE: logging?

__all__: list = []
