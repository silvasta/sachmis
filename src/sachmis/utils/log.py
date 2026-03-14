from .print import printer
import sys
from functools import wraps
from pathlib import Path
from types import SimpleNamespace

import typer
from loguru import logger

from .path import find_project_root, pyproject_log_section

_is_configured = False


def setup_logging(
    project_root: Path | None = None,
    log_level_override: str | None = None,
    log_to_file: bool = True,
    quiet: bool = False,
):
    """Configures Loguru based on pyproject.toml settings"""

    global _is_configured
    if _is_configured:
        return logger

    if project_root is None:
        project_root: Path = find_project_root("pyproject.toml")

    try:  # Parse config from pyproject.toml file
        log_config: SimpleNamespace = pyproject_log_section()
        # values
        log_level = log_config.level
        log_filename = log_config.file_name
        rotation = log_config.rotation
        retention = log_config.retention
        printer.md("...loading log config loaded from **pyproject.toml**")

    except AttributeError:
        log_level = "INFO"
        rotation = "5 MB"
        retention = "1 week"
        log_filename = "debug.log"
        printer.title("Using default log configs")

    if log_level_override is not None:
        log_level: str = log_level_override

    logger.remove()

    if not quiet:
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            colorize=True,
        )

    if log_to_file:
        log_dir: Path = project_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path: Path = log_dir / log_filename

        logger.add(
            log_path,
            level="DEBUG",  # Always keep debug detail in files
            rotation=rotation,
            retention=retention,
            compression="zip",
            backtrace=True,  # Note: this can reveal sensitive data!
            diagnose=True,  # Shows variable values in logs!
            enqueue=True,  # Thread-safe
        )

    if not quiet and not log_to_file:
        print("Warning: Logging is completely disabled.")

    _is_configured = True
    return logger


def logger_catch(func):
    """Typer decorater BELOW 'app.command()', catch errors and log them via Loguru.
    Ensures metadata is preserved and errors are handled globally."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # reraise=False ensures the app doesn't crash with a standard Python traceback
        # but Loguru still writes the full error to your sinks.
        with logger.catch(reraise=False):
            return func(*args, **kwargs)

    return wrapper


def logging_callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show debug logs"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Disable terminal output"),
):
    """Setup logging for Typer CLI, works across different entry points
    Usage: app.callback()(logging_callback)"""
    # NOTE: currently not used, it was overriden by main_callback and is now merged inside there
    level: str | None = "DEBUG" if verbose else None
    setup_logging(log_level_override=level, quiet=quiet)
