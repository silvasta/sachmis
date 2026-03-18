from pathlib import Path

from pydantic import Field
from silvasta.data.files import File


class Prompt(File):
    text: Path
    files: list[Path] = Field(default_factory=list)  # TODO: file management
    images: list[Path] = Field(default_factory=list)  # TODO: file management


class Response(File):
    full_response: Path  # TODO: file management
    id: str
    content: str
    usage: dict = Field(default_factory=dict)


class UploadFile(File):
    """Local file for upload and usage in prompt"""

    name: str
    category: str
    topic: str
    local_path: Path  # REMOVE: relative from local filedir (.camp/files)

    @property
    def description(self):
        return f"[blue]{self.category}[/]-[green]{self.topic}[/]-[white]{self.local_path.name}[/]"


class XaiUploadFile(UploadFile):
    # from xAI upload, needed for prompt attach
    x_id: str | None = None


class GoogleUploadFile(UploadFile):
    # from Goole upload, needed for prompt attach
    g_uri: str | None = None
    g_mime_type: str | None = None
