from sstcore.utils.print import ColorBox
from sachmis.core.model import Model
import uuid
from itertools import cycle

from rich.table import Table

from sachmis.config import models
from sachmis.utils import printer

for model in models.all():
    printer(model.cli)

printer(f"{uuid.uuid4()}")


c: ColorBox = printer.colorbox()


def model_table(
    header: str = "Table with all Active Models",
    show_header=True,
    title=None,
):
    """load base paths from file, check existence, print result"""

    printer.title(header)
    table = Table(
        title=title,
        show_header=show_header,
        expand=True,
        border_style="cyan",
    )
    table.add_column("Unique")
    table.add_column("Name")
    table.add_column("API Request Alias")

    colors: list[str] = ["cyan", "magenta", "yellow", "green", "white"]

    for model, color in zip(models.family(), cycle(colors), strict=False):
        table.add_row(model.unique, str(model), model.api_name, style=color)

    printer(table)


def model_previous_id(
    models: list[Model],
    header: str = "Previous ID Table",
    show_header=True,
    title=None,
):
    """load base paths from file, check existence, print result"""

    printer.title(header)
    table = Table(
        title=title,
        show_header=show_header,
        expand=True,
        border_style="cyan",
    )
    table.add_column("Status", justify="center")
    table.add_column("Model")

    for model in models:
        status: str = c.g("✅") if model.has_previous_id else c.r("")
        table.add_row(status, model.model.cli)

    printer(table)


model_table()
