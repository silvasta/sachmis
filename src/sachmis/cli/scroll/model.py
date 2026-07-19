from itertools import cycle

from rich.table import Table
from sstcore import printer
from sstcore.utils.color import ColorBox

from ...config import models
from ...core.model import Model

c = ColorBox()


def conversation_transition_result(  # MOVE: where?
    prompt: str, response: str, result: bool, from_prompt: bool
):
    source = f"Prompt {c.cyan(prompt)}"
    target = f"Response {c.magenta(response)}"

    if not from_prompt:
        target, source = source, target

    text = f"{source} --> {target}"

    if result:
        printer.success(text)
    else:
        printer.danger(text)


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


def model_family_table(
    selection: list[models.ModelFamily] | None = None,
    header: str = "Table with all Active Models",
    show_header=True,
    title=None,
):
    """load base paths from file, check existence, print result"""

    displayed_models: list[models.ModelFamily] = selection or models.family()

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

    for model, color in zip(displayed_models, cycle(colors), strict=False):
        table.add_row(model.unique, str(model), model.api_name, style=color)

    printer(table)
