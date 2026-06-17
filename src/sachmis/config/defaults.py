from typing import Literal

from pydantic import BaseModel, Field
from sstcore.config import SstDefaults

### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### Models
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


class ModelParam(BaseModel):
    """Base for all models"""


class GrokParam(ModelParam):
    timeout: int = 3600
    store_messages: bool = True
    n_agents: Literal[0, 4, 16] = 4  # 0 -> launch picker


class GeminiParam(ModelParam):
    # -1 = dynamic, 0 = off, 1024 = high
    thinking_budget: int | None = -1


class ModelToggle(BaseModel):
    dummy: bool = False
    grok: bool = True
    gemini: bool = True


### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### Retry
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


class TenacityDefaults(BaseModel):
    max_attempts: int = 5

    wait_exponential: dict[str, int] = {
        "multiplier": 60,  # Base 1 minute
        "min": 300,  # Minimum wait: 300 seconds (5 minutes)
        "max": 1800,  # Maximum wait: 1800 seconds (30 minutes)
    }


### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### Context
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


class ContextBase(BaseModel):
    swallow: bool = False


class ContextDefaults(BaseModel):  # TASK: unify strategy
    """Global Control of ContextManager.__exit__ behaviour (and more?)"""

    forest_error: ContextBase = Field(default_factory=ContextBase)
    forest_end: ContextBase = Field(default_factory=ContextBase)

    tree_error: ContextBase = Field(default_factory=ContextBase)
    tree_end: ContextBase = Field(default_factory=ContextBase)

    data_error_arboreal: ContextBase = Field(
        default_factory=lambda: ContextBase(swallow=True)
    )
    data_error_sachmis: ContextBase = Field(
        default_factory=lambda: ContextBase(swallow=True)
    )
    data_end: ContextBase = Field(default_factory=ContextBase)


### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### App
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


# class LogAndPrint(BaseModel):  # REMOVE: or find usage
#     printer: bool = False
#     log: bool = True
#
#
# class LogAndPrintParam(BaseModel):  # REMOVE: or find usage
#     PLACEHOLDER: LogAndPrint = Field(
#         default_factory=lambda: LogAndPrint(printer=True, log=True)
#     )


class DebugToggle(BaseModel):
    subapp: bool = True  # PARAM: switch! debug app not shown per default

    # REMOVE:
    pause_at_tree_extract: bool = True
    print_at_tree_extract: bool = True
    draw_tree_at_back_attach: bool = True

    printer_debugs: bool = False


class MissingDefaults(BaseModel):
    """Behaviour for Action on Missing"""

    # TODO: check where this is active!
    biome: Literal["create", "raise", "prompt"] = "prompt"


default_dot_env_content = """
# Fill at least 1, delete others
XAI_API_KEY=
GEMINI_API_KEY=
"""


### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### The Assembly
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


class Defaults(SstDefaults):
    """Composition of App and Model Defaults controllable by JSON"""

    # Model and Task
    gemini: GeminiParam = Field(default_factory=GeminiParam)
    grok: GrokParam = Field(default_factory=GrokParam)
    active: ModelToggle = Field(default_factory=ModelToggle)

    # Pipeline
    tenacity: TenacityDefaults = Field(default_factory=TenacityDefaults)

    # Context
    context: ContextDefaults = Field(default_factory=ContextDefaults)

    # App
    # log_and_print: LogAndPrintParam = Field(default_factory=LogAndPrintParam)
    debug: DebugToggle = Field(default_factory=DebugToggle)
    on_missing: MissingDefaults = Field(default_factory=MissingDefaults)
    dot_env_content: str = default_dot_env_content
    topic: str = "Time to select a Topic"
