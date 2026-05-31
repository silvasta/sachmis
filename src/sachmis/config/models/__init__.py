from loguru import logger

from ...config import SachmisConfig, get_config
from ...config.defaults import ModelToggle
from ...utils import printer
from .dummy import DummyFamily
from .family import ModelFamily
from .gemini import Geminis
from .grok import Groks

# TASK: State Selector with active Models


def model_family() -> list[ModelFamily]:
    """Load combination of all Model Families"""
    config: SachmisConfig = get_config()

    toggle: ModelToggle = config.defaults.debug.model

    # TODO: new helper for printer, colorizor or so

    if any([not toggle.dummy, toggle.grok, toggle.gemini]):
        title: str = "ModelToggle away from default values!"
        printer.scroll(items=[printer.red(title), f"{toggle=}"])
        msg = f"Check 'config.defaults.debug.model': {config.setting_file=}"
        logger.warning(msg)

    return [
        *([dummy for dummy in DummyFamily] if toggle.dummy else []),
        *([grok for grok in Groks] if toggle.grok else []),
        *([gemini for gemini in Geminis] if toggle.gemini else []),
    ]


__all__: list[str] = [
    "ModelFamily",
    "Groks",
    "Geminis",
    "DummyFamily",
    "model_family",
]
