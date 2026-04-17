from pathlib import Path

from boltons.strutils import slugify
from pydantic import BaseModel, Field

from sachmis.data.files import UploadFile


class Prompt(BaseModel):
    topic: str
    text: str
    files: list[UploadFile] = Field(default_factory=list)
    images: list[Path] = Field(default_factory=list)

    # NEXT: local file rollout
    @property
    def slug_topic(self):
        return slugify(self.topic)
