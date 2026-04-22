from pydantic import Field
from pydantic_settings import BaseSettings
from silvasta.config import SstDefaults


class TenacityDefaults(BaseSettings):
    max_attempts: int = 3
    wait_exponential: dict[str, int] = {
        "multiplier": 1,
        # NEXT: check gemini chat, this few seconds are ridicoulous!
        "min": 2,
        "max": 10,
    }


class Defaults(SstDefaults):
    tenacity: TenacityDefaults = Field(default_factory=TenacityDefaults)
    topic: str = "Default Topic"
    dot_env_content: str = """# Fill at least 1, delete others
XAI_API_KEY=
GEMINI_API_KEY=
"""
