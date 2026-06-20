from pathlib import Path
from typing import Any

import typer
from sstcore.exceptions import TuiSelectorError

from sachmis.cli.app import app
from sachmis.exceptions import ArborealFileError, SachmisLaunchError
from sachmis.utils import printer

exceptions: dict[Exception, dict[str, Any]] = {
    typer.Exit: {},
    typer.Abort: {},
    TuiSelectorError: {},
    ArborealFileError: {
        "msg": "Arbo Failed",
        "arboreal": "Tree",
        "file": Path(),
    },
    SachmisLaunchError: {},
}


def main(stress_test=True):
    """Run all Exception UI tests"""
    breakpoint()
    for index, error in enumerate(exceptions.keys()):
        error_name: str = printer.colors.red(error.__name__)
        printer.debug(f"Testing: {error_name}")
        run_app(index, stress_test, error_name)


@app.command()
def throw(index: int):
    error, kwargs = list(exceptions.items())[index]
    raise error(**kwargs)


def run_app(index: int, stress_test=True, error_name: str = ""):
    printer(f"running {index=}, {stress_test=}")
    try:
        app(["throw", str(index)])

    except SystemExit as e:
        msg = f"SafeTyper executed clean shutdown with exit code: {e.code}"
        printer.debug(msg, title=error_name)

    except Exception as e:
        if stress_test:  # No catch, simulate real pipeline
            raise
        printer.danger(f"Test failed with unexpected traceback: {e}")


if __name__ == "__main__":
    main()
