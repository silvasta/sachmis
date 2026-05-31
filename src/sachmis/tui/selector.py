from pathlib import Path

from loguru import logger
from sstcore.data import FileRegistry
from sstcore.exceptions import FailedSelectionError
from sstcore.tui import ListSelectorApp, TreeSelectorApp

from ..config import models as fam
from ..utils.parse import parse_raw_models


def model_selector(
    models: list[fam.ModelFamily] | None = None,
    multi_select: bool = True,
) -> list[fam.ModelFamily]:
    models: list[fam.ModelFamily] = models or fam.model_family()

    items: dict[str, str] = {model.unique: model.api_name for model in models}

    tui = ListSelectorApp(items=items, multi_select=multi_select)
    selected_models: list[str] | None = tui.run()

    if selected_models:
        logger.success(f"Selected {len(selected_models)=}")
        logger.debug(f"{selected_models=}")

        return parse_raw_models(selected_models)

    raise FailedSelectionError("No valid models parsed from input...")


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
    raise FailedSelectionError


def multi_line_selector[T](items: dict[T, str] | list[T] | set[T]) -> list[T]:

    if selected := ListSelectorApp(items=items, multi_select=True).run():
        logger.success(f"Selected {len(selected)} elements")
        return selected
    raise FailedSelectionError


def single_line_selector[T](items: dict[T, str] | list[T] | set[T]) -> T:

    if selected := ListSelectorApp(items=items, multi_select=False).run():
        logger.success(f"Selected: {(item := selected[0])=}")
        return item
    raise FailedSelectionError
