from pathlib import Path

from pydantic import BaseModel, Field


class Response(BaseModel):
    full_response: Path
    id: str
    content: str = ""
    usage: dict = Field(default_factory=dict)
    # NEXT: local file rollout
