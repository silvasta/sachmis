from pathlib import Path

from loguru import logger
from sstcore.data import FileRegistry
from sstcore.exceptions import TuiSelectorError
from sstcore.tui import ListSelectorApp, TreeSelectorApp

from ..config.models import ModelFamily
from ..config.models import family as all_models
from ..data.conversation import SelectedSproutData, SproutSelectData
from ..utils import printer
from ..utils.parse import parse_raw_models


def model_family(
    models: list[ModelFamily] | None = None,
    multi_select: bool = True,
) -> list[ModelFamily]:
    """Select from list of raw Models"""
    models: list[ModelFamily] = models or all_models()

    items: dict[str, str] = {model.unique: model.api_name for model in models}

    tui = ListSelectorApp(items=items, multi_select=multi_select)
    selected_models: list[str] | None = tui.run()

    if selected_models:
        logger.success(f"Selected {len(selected_models)=}")
        logger.debug(f"{selected_models=}")

        return parse_raw_models(selected_models)

    raise TuiSelectorError("No valid models parsed from input...")


def model_from_scan(
    models: list[SproutSelectData], multi_select: bool = True
) -> list[SelectedSproutData]:
    """Select from list of Models with stored Information"""

    items: dict[str, str] = {
        model.selector_uuid: model.selector_display_name
        for model in models  # show value, return key
    }

    tui = ListSelectorApp(items=items, multi_select=multi_select)
    selected_uuids: list[str] | None = tui.run()

    if selected_uuids:
        selected_models: list[SelectedSproutData] = [
            SelectedSproutData.from_scan(model)
            for model in models
            if model.selector_uuid in set(selected_uuids)
        ]
        logger.success(f"Selected {len(selected_models)=}")
        printer(selected_models)

        return selected_models

    raise TuiSelectorError("No valid models parsed from input...")


def file_registry(
    files: FileRegistry, root_name: str | None = None
) -> list[Path]:
    """Select from FileRegistry by displaying Tree representation"""

    if selected_files := TreeSelectorApp(sst_tree=files.tree(root_name)).run():
        logger.success(f"Selected {len(selected_files)=}")
        return selected_files

    logger.warning("Selector closed with 0 selected Files")

    return []


def role_path(roles: list[Path]) -> Path:
    """Select from Paths displayed by name and get 1 selected back"""

    items: dict[Path, str] = {role: role.name for role in roles}
    # LATER: provide advanced setup, statistic and selection

    if selected := ListSelectorApp(items=items, multi_select=False).run():
        logger.success(f"Selected {(role := Path(selected[0])).name}")
        return role
    raise TuiSelectorError


def multi_linear[T](items: dict[T, str] | list[T] | set[T]) -> list[T]:
    """Select from linear Container and get multiple Elements back"""

    if selected := ListSelectorApp(items=items, multi_select=True).run():
        logger.success(f"Selected {len(selected)} elements")
        return selected
    raise TuiSelectorError


def single_linear[T](items: dict[T, str] | list[T] | set[T]) -> T:
    """Select from linear Container and get 1 Element back"""

    if selected := ListSelectorApp(items=items, multi_select=False).run():
        logger.success(f"Selected: {(item := selected[0])=}")
        return item
    raise TuiSelectorError
