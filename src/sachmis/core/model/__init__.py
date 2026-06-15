"""
Model for Execution - The Purpose of the entire Pipeline

The Base and the Controller of the Execution is in 'agent'

Gemini and Grok provide custom adapters for their APIs

'launch' is the collector for a general pipeline interface

"""

__all__: list[str] = [
    "Model",
    "Grok",
    "Gemini",
    "launch",
]
from . import launch
from .agent import Model
from .gemini import Gemini
from .grok import Grok
