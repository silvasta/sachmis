from sstcore.tui import ListSelectorApp

from ..config.model import ModelFamily, get_all_models


def model_selector(multi_select: bool = True, with_dummy=False) -> list[str]:

    models: list[ModelFamily] = get_all_models(with_dummy)
    items: dict[str, str] = {model.unique: model.api_name for model in models}

    tui = ListSelectorApp(items=items, multi_select=multi_select)
    selected_models: list[str] | None = tui.run()

    if not selected_models:
        raise ValueError("No valid models parsed from input...")

    return selected_models
