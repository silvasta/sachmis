from ..utils import printer
from .defaults import Defaults, ModelToggle
from .manager import SachmisConfig, get_config
from .models import DummyFamily, Geminis, Groks, ModelFamily
from .names import Names
from .paths import Paths
from .settings import Settings

__all__: list[str] = [
    "get_config",
    "SachmisConfig",
    "Paths",
    "Settings",
    "Names",
    "Defaults",
    "model_family",
    "model_uniques",
    "model_api_names",
]


# MOVE: prints to CLI


# TASK: State Selector with active Models
def model_family() -> list[ModelFamily]:
    """Load combination of all Model Families"""
    config: SachmisConfig = get_config()

    toggle: ModelToggle = config.defaults.debug.model

    # TODO: new helper for printer, colorizor or so; done -> apply

    if any([not toggle.dummy, toggle.grok, toggle.gemini]):
        title: str = "ModelToggle away from default values!"
        printer.scroll(items=[printer.red(title), f"{toggle=}"])

    return [
        *([dummy for dummy in DummyFamily] if toggle.dummy else []),
        *([grok for grok in Groks] if toggle.grok else []),
        *([gemini for gemini in Geminis] if toggle.gemini else []),
    ]


def model_uniques() -> list[str]:
    return [model.unique for model in model_family()]


def model_api_names() -> list[str]:
    return [model.api_name for model in model_family()]
