from pathlib import Path

from loguru import logger
from sstcore.data import FileRegistry
from sstcore.tui import ListSelectorApp, TreeSelectorApp

from ..config import SachmisConfig, get_config
from ..config.model import ModelFamily, get_all_models
from ..utils.parse import parse_raw_models


def model_selector(
    models: list[ModelFamily] | None = None,
    multi_select: bool = True,
    with_dummy=False,
) -> list[ModelFamily]:

    models: list[ModelFamily] = models or get_all_models(with_dummy)
    items: dict[str, str] = {model.unique: model.api_name for model in models}

    tui = ListSelectorApp(items=items, multi_select=multi_select)
    selected_models: list[str] | None = tui.run()

    if not selected_models:
        # TODO: better error, or just forward None
        raise ValueError("No valid models parsed from input...")

    return parse_raw_models(selected_models)


def file_selector(  # LATER: create SstFileTree? + Selector itself there!
    files: FileRegistry, root_name: str | None = None
) -> list[Path]:
    if not root_name:
        config: SachmisConfig = get_config()
        if config.paths.in_forest:
            root_name: str = config.paths.base_dir.name
        else:
            root_name: str = "SachmisFileSelector"  # PARAM:

    tui = TreeSelectorApp(sst_tree=files.tree(root_name))
    selected_files: list[Path] | None = tui.run()

    if not selected_files:
        logger.warning("Selector closed with 0 selected Files")
        return []

    return selected_files


def role_selector(roles: list[Path]) -> Path | None:

    items: dict[Path, str] = {role: role.name for role in roles}

    # TODO: provide 2 separated lists, local/global role

    tui = ListSelectorApp(items=items, multi_select=False)
    selected: list[Path] | None = tui.run()

    if not selected:
        logger.warning("No valid role selected...")
        role = None
    else:
        role: Path = Path(selected[0])

    return role


def linear_selector[T](
    items: dict[T, str] | list[T] | set[T], multiselect=False
) -> list[T] | None:

    tui = ListSelectorApp(items=items, multi_select=multiselect)
    selected: list[T] | None = tui.run()

    if not selected:
        logger.warning("Nothing selected...")
        selected = None

    return selected
