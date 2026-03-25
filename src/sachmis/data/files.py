from pathlib import Path

from pydantic import BaseModel, Field
from silvasta.data.files import File


class Prompt(BaseModel):
    topic: str
    text: str
    # LATER: files: Path or UploadFile? or just str
    files: list["UploadFile"] = Field(default_factory=list)
    images: list[Path] = Field(default_factory=list)


class Response(BaseModel):
    full_response: Path
    id: str
    content: str = ""
    usage: dict = Field(default_factory=dict)


class UploadFile(File):
    """Local file for upload and usage in prompt"""

    name: str
    category: str = ""
    topic: str = ""
    # local_path: Path LATER: relative from local filedir (.camp/files)??

    @property
    def description(self):
        return f"[blue]{self.category}[/]-[green]{self.topic}[/]-[white]{self.local_path.name}[/]"


class XaiUploadFile(UploadFile):
    # from xAI upload, needed for prompt attach
    x_id: str | None = None


# TASK: how to save this again into 1 UploadFile???


class GoogleUploadFile(UploadFile):
    # from Goole upload, needed for prompt attach
    g_uri: str | None = None
    g_mime_type: str | None = None

    # TASK: manage online files
    # - do upload at first usage from file
    # ...manual upload possibility probably still needed?
    # def manage_online_forest_files( self, xai=False, google=False, task: Literal["push", "show", "delete"] = "show",):
    #     uploaders: list[FileUploader] = []
    #     if xai:
    #         uploaders.append(XaiUploader())
    #     if google:
    #         uploaders.append(GoogleUploader())
    #     for uploader in uploaders:
    #         match task:
    #             case "push":
    #                 for file in self.forest.files:
    # IMPORTANT: use this during runtime, e.g. in Fire or Script
    #                     uploader.upload_local_file(
    #                         file, base_path=self.config.file_dir
    #                     )
    #             case "show":
    #                 uploader.show_all_files()
    #             case "delete":
    #                 uploader.delete_all_uploaded_files()
