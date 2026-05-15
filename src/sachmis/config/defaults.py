from typing import Literal

from pydantic import BaseModel, Field
from sstcore.config import SstDefaults


class TenacityDefaults(BaseModel):
    max_attempts: int = 5

    wait_exponential: dict[str, int] = {
        "multiplier": 60,  # Base 1 minute
        "min": 300,  # Minimum wait: 300 seconds (5 minutes)
        "max": 1800,  # Maximum wait: 1800 seconds (30 minutes)
    }


class ModelParam(BaseModel):
    value: int = 4


class GrokParam(ModelParam):
    timeout: int = 3600
    store_messages: bool = True
    n_agents: Literal[0, 4, 16] = 4  # 0 -> launch picker


class GeminiParam(ModelParam):
    # -1 = dynamic, 0 = off, 1024 = high
    thinking_budget: int | None = -1


default_dot_env_content = """
# Fill at least 1, delete others
XAI_API_KEY=
GEMINI_API_KEY=
"""


class ContextBase(BaseModel):
    swallow: bool = False


class ContextParam(BaseModel):
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


class LogAndPrintBase(BaseModel):
    printer: bool = False
    log: bool = True


class LogAndPrintParam(BaseModel):
    conversation_bag: LogAndPrintBase = Field(
        default_factory=lambda: LogAndPrintBase(printer=True, log=True)
    )
    data_prompt_attach: LogAndPrintBase = Field(
        default_factory=lambda: LogAndPrintBase(printer=True, log=True)
    )


class Defaults(SstDefaults):
    # Model and Task
    model_base: ModelParam = Field(default_factory=ModelParam)
    gemini: GeminiParam = Field(default_factory=GeminiParam)
    grok: GrokParam = Field(default_factory=GrokParam)

    # Pipeline
    tenacity: TenacityDefaults = Field(default_factory=TenacityDefaults)

    # Context
    context: ContextParam = Field(default_factory=ContextParam)

    # util
    log_and_print: LogAndPrintParam = Field(default_factory=LogAndPrintParam)
    dot_env_content: str = default_dot_env_content
    topic: str = "Time to select a Topic"
