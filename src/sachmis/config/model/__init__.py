from .family import ModelFamily
from .gemini import Geminis
from .grok import Groks

# TASK: create all_families here?
__all__: list[type[ModelFamily]] = [
    ModelFamily,
    Groks,
    Geminis,
]
