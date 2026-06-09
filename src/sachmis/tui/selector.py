from pathlib import Path

from loguru import logger
from sstcore.data import FileRegistry
from sstcore.exceptions import TuiSelectorError
from sstcore.tui import ListSelectorApp, TreeSelectorApp

from sachmis.utils import printer

from ..config.models import ModelFamily, ModelSelectData
from ..config.models import family as all_models
from ..utils.parse import parse_raw_models


def model_selector(
    models: list[ModelFamily] | None = None,
    multi_select: bool = True,
) -> list[ModelFamily]:
    models: list[ModelFamily] = models or all_models()

    items: dict[str, str] = {model.unique: model.api_name for model in models}

    tui = ListSelectorApp(items=items, multi_select=multi_select)
    selected_models: list[str] | None = tui.run()

    if selected_models:
        logger.success(f"Selected {len(selected_models)=}")
        logger.debug(f"{selected_models=}")

        return parse_raw_models(selected_models)

    raise TuiSelectorError("No valid models parsed from input...")


def model_selector_with_dataclass(
    models: list[ModelSelectData],
    multi_select: bool = True,
) -> list[ModelSelectData]:

    items: dict[str, str] = {model.uuid: model.show for model in models}

    tui = ListSelectorApp(items=items, multi_select=multi_select)
    selected_uuids: list[str] | None = tui.run()

    if selected_uuids:
        selected_models: list[ModelSelectData] = [
            model  # Filter all by uuid
            for model in models
            if model.uuid in set(selected_uuids)
        ]
        logger.success(f"Selected {len(selected_models)=}")
        printer(selected_models)

        return selected_models

    raise TuiSelectorError("No valid models parsed from input...")


def file_selector(
    files: FileRegistry, root_name: str | None = None
) -> list[Path]:

    if selected_files := TreeSelectorApp(sst_tree=files.tree(root_name)).run():
        logger.success(f"Selected {len(selected_files)=}")
        return selected_files

    logger.warning("Selector closed with 0 selected Files")

    return []


# TODO: provide 2 separated lists, local/global role
def role_selector(roles: list[Path]) -> Path:
    items: dict[Path, str] = {role: role.name for role in roles}

    if selected := ListSelectorApp(items=items, multi_select=False).run():
        logger.success(f"Selected {(role := selected[0]).name}")
        return role
    raise TuiSelectorError


def multi_line_selector[T](items: dict[T, str] | list[T] | set[T]) -> list[T]:

    if selected := ListSelectorApp(items=items, multi_select=True).run():
        logger.success(f"Selected {len(selected)} elements")
        return selected
    raise TuiSelectorError


def single_line_selector[T](items: dict[T, str] | list[T] | set[T]) -> T:

    if selected := ListSelectorApp(items=items, multi_select=False).run():
        logger.success(f"Selected: {(item := selected[0])=}")
        return item
    raise TuiSelectorError
