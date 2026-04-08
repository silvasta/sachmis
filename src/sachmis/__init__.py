# TASK:
# - Thunder and Fire structure
# - Check structured response
# - arboreal


from importlib.metadata import PackageNotFoundError, version

try:  # Show pyproject.toml package name
    __version__: str = version("sachmis")
except PackageNotFoundError:
    __version__ = "unknown"

# NOTE: logging?

__all__: list = []
