from typer import Typer

from .bases import app as bases_app
from .files import app as files_app
from .forest import app as forest_app
from .show import app as show_app

__all__: list[Typer] = [
    bases_app,
    files_app,
    forest_app,
    show_app,
]
