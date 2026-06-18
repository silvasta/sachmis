from loguru import logger

from ..defaults import ModelToggle
from ..manager import get_config
from .dummy import DummyFamily
from .family import ModelFamily
from .gemini import Geminis
from .grok import Groks

__all__: list[str] = [
    "ModelFamily",
    "Groks",
    "Geminis",
    "DummyFamily",
]


def select(dummy=False, grok=False, gemini=False) -> list[ModelFamily]:
    """Load combination of all Model Families"""

    return [
        *([dummy for dummy in DummyFamily] if dummy else []),
        *([grok for grok in Groks] if grok else []),
        *([gemini for gemini in Geminis] if gemini else []),
    ]


def all() -> list[ModelFamily]:
    """Load combination of all Model Families"""

    return select(dummy=True, grok=True, gemini=True)


def family() -> list[ModelFamily]:
    """Filter combination of all Model Families by Defaults from json"""

    toggle: ModelToggle = get_config().defaults.active

    if any([toggle.dummy, not toggle.grok, not toggle.gemini]):
        logger.warning(f"ModelToggle away from default values! {toggle=}")

    return select(toggle.dummy, toggle.grok, toggle.gemini)


# IDEA: @cache?
def uniques() -> set[str]:
    return {model.unique for model in family()}


def names() -> list[str]:
    return [str(model) for model in family()]


def api_names() -> list[str]:
    return [model.api_name for model in family()]
