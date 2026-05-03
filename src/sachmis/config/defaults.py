from typing import Literal

from pydantic import BaseModel, Field
from sstcore.config import SstDefaults


class TenacityDefaults(BaseModel):
    max_attempts: int = 3
    wait_exponential: dict[str, int] = {
        "multiplier": 1,
        # TASK: check gemini chat, this few seconds are ridicoulous!
        "min": 2,
        "max": 10,
    }


class ModelParam(BaseModel):
    """Specific values and defaults, depending on Model and ModelFamily"""


class GrokParam(ModelParam):
    timeout: int = 3600
    store_messages: bool = True
    n_agents: Literal[0, 4, 16] = 4  # 0 intended for interactive?


class GeminiParam(ModelParam):
    # -1 = dynamic, 0 = off, 1024 = high
    thinking_budget: int | None = -1


# TASK: attach ModelParam to Defaults?


class Defaults(SstDefaults):
    tenacity: TenacityDefaults = Field(default_factory=TenacityDefaults)
    topic: str = "Default Topic"
    dot_env_content: str = """# Fill at least 1, delete others
XAI_API_KEY=
GEMINI_API_KEY=
"""
    gemini: GeminiParam = Field(default_factory=GeminiParam)
    grok: GrokParam = Field(default_factory=GrokParam)
