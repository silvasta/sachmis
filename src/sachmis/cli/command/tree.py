from pathlib import Path

import typer
from silvasta.cli.setup import logger_catch

from sachmis.data import DataManager
from sachmis.utils.print import printer


@logger_catch
def tree(ctx: typer.Context, sprout: Path):
    """Create new sprout from existing response in new folder"""

    # NEXT: how to branch?

    data: DataManager = ctx.obj["data"]
    data.load_forest()
    printer.title("Forest loaded, start creating new sprout")
    data.tree(sprout)
