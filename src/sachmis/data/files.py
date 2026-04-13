from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Literal

from loguru import logger
from pydantic import BaseModel, Field
from silvasta.data.files import SstFile


class Prompt(BaseModel):
    topic: str
    text: str
    files: list["UploadFile"] = Field(default_factory=list)
    images: list[Path] = Field(default_factory=list)
    # TODO: local file rollout


class Response(BaseModel):
    full_response: Path
    id: str
    content: str = ""
    usage: dict = Field(default_factory=dict)
    # TODO: local file rollout


class UploadState(BaseModel):  # PLUG:
    last_upload: datetime = Field(default_factory=datetime.now)

    @property
    def age(self) -> timedelta:
        """Return time since last upload of file"""
        return datetime.now() - self.last_upload


class XaiUploadState(UploadState):
    # identifier
    # IMPORTANT: this as param somewhere avaliable everywhere -> config
    target: Literal["xai"] = "xai"
    # specific states
    x_id: str


class GoogleUploadState(UploadState):
    # identifier
    # IMPORTANT: this as param somewhere avaliable everywhere -> config
    target: Literal["google"] = "google"
    # specific states
    g_uri: str
    g_mime_type: str
    g_name: str

    @property
    def is_outdated(self) -> bool:
        """Files are deleted after 48 hours"""
        return self.age > timedelta(hours=47)  # PARAM:


type RemoteState = Annotated[
    XaiUploadState | GoogleUploadState,  # PLUG:
    Field(discriminator="target"),
]


class UploadFile(SstFile):
    """Local file for upload and usage in prompt"""

    remote_states: dict[str, RemoteState] = Field(default_factory=dict)

    @property
    def remotes(self) -> str:
        # FIX: unreadable
        parts: list[str] = [
            f"[white]{self.name}[/]",
            f"[dim]Uploads: {list(self.remote_states.keys())}[/dim]",
        ]
        return " - ".join(parts)

    @property
    # MERGE: somehow color/raw print
    def _remotes(self) -> str:
        parts: list[str] = [
            f"{self.name}",
            f"remotes: {list(self.remote_states.keys())}",
        ]
        return " - ".join(parts)

    @property
    def description(self):
        # MOVE: to silvasta|project.config.setting.Names
        parts: list[str] = [
            f"[blue]{self.name}[/]",
            f"[dim]{self.first_tracked}[/]",
            f"[white]{self.last_updated}[/]",
        ]
        return "-".join(parts)

    def attach_remote(self, state: RemoteState):
        """Attach new remote states"""
        self.remote_states[state.target] = state
        self.touch()

    def find_remote(self, target: str) -> RemoteState | None:
        """Find and get remote state for 'target', None for not found"""
        return self.remote_states.get(target)

    def has_remote(self, target: str) -> bool:
        """Check if remote state for 'target' is avaliable"""
        return self.find_remote(target) is not None

    def get_remote_state(self, target: str) -> RemoteState:
        """Get remote state for 'target' or raise"""
        logger.debug(f"extracting for {target=}")
        if (remote_state := self.remote_states.get(target)) is None:
            logger.warning(self._remotes)
            raise AttributeError(f"No remote state for {target} avaliable!")
        return remote_state

    def remove_remote(self, target: str) -> RemoteState | None:
        """Remove 'target' remote_states, get value or None for not existing"""
        if (remote_state := self.remote_states.pop(target, None)) is None:
            logger.warning(f"Attempt to remove not existing remote: {target=}")
        else:
            self.touch()
            logger.debug(f"removed {target} from remote_states")
        return remote_state
