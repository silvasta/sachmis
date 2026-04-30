from .dummy import DummyFamily
from .family import ModelFamily
from .gemini import Geminis
from .grok import Groks

# TASK: create all_families here?


def get_all_models(with_dummy=False) -> list[ModelFamily]:
    return [
        *[grok for grok in Groks],
        *[gemini for gemini in Geminis],
        *([dummy for dummy in DummyFamily] if with_dummy else []),
    ]


__all__: list[str] = [
    "ModelFamily",
    "Groks",
    "Geminis",
    "DummyFamily",
]
