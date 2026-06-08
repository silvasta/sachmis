import time

from loguru import logger
from sstcore.exceptions import TuiSelectorError

from ...config import SachmisConfig, get_config
from ...config.models import ModelFamily
from ...data.handler import FileRollout
from ...tui.selector import model_selector
from ...utils.parse import parse_raw_models
from ...utils.print import printer
from .. import args

config: SachmisConfig = get_config()


def rollout(  # TASK: this as selector of current file tree!
    # Arguments
    id: int,
    models: args.Models = None,
    # sprout: args.Sprout = False,
    # Options for task selection
    pick_model: args.PickModel = False,
):
    """Test File to Filesystem Mapping for write only files"""

    if True:
        printer.special("Comming Soon")
        return
    # TASK:
    # -> handler figures out tree_id or root
    # state loads c_id from Tree at init
    # -> to handler
    # - models, select
    handler = FileRollout()

    models: list[ModelFamily] = _prepare_model_args(
        models, pick_model, handler
    )
    printer.panel("Los...", frame="cyan")
    printer.header([model.cli for model in models], frame="purple")
    time.sleep(1)
    printer.panel("..Fertig", frame="green")

    printer.success("Models finished to run, storing data, au revoir!")

    for model in models:
        handler.process(model, "sachmis", 3 * id, 7 * id)


def _prepare_model_args(
    models: list[str] | None, pick_model: bool, handler: FileRollout
) -> list[ModelFamily]:
    printer.title("Selecting Models...")

    if models and (parsed_models := parse_raw_models(models)):
        printer.header(f"...{len(parsed_models)} selected for pipeline")
        return parsed_models

    if len(_models := handler.status.models(pick_model)) == 1:
        printer.title(f"Single Model {_models[0].cli}", frame="magenta")
        return _models

    if selected := model_selector(models=_models, multi_select=True):
        logger.debug(f"{selected=}")
        return selected

    raise TuiSelectorError()
