from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Literal, Self

from boltons.strutils import slugify
from loguru import logger
from pydantic import BaseModel, Field
from silvasta.config import get_config
from silvasta.data.files import FileRegistry, FileSystemManager, SstFile

from sachmis.config import SachmisConfig


class UploadState(BaseModel):  # PLUG:
    last_upload: datetime = Field(default_factory=datetime.now(UTC))

    @property
    def age(self) -> timedelta:
        """Return time since last upload of file"""
        return datetime.now(UTC) - self.last_upload


class XaiUploadState(UploadState):
    target: Literal["xai"] = "xai"

    x_id: str


class GoogleUploadState(UploadState):
    target: Literal["google"] = "google"

    g_uri: str
    g_mime_type: str
    g_name: str

    @property
    def is_outdated(self) -> bool:
        """Files are deleted after 48 hours"""
        return self.age > timedelta(hours=47)  # PARAM:


# IDEA: move state to config.param? or simply data.states

type RemoteState = Annotated[
    XaiUploadState | GoogleUploadState,  # PLUG:
    Field(discriminator="target"),
]


class UploadFile(SstFile):
    """Local file for upload and usage in prompt"""

    remote_states: dict[str, RemoteState] = Field(default_factory=dict)

    _name_at_load: str = Field(default_factory=lambda path: path.name)

    @classmethod
    def with_slug_name(cls, path: Path) -> Self:
        name_at_load: str = path.name
        slug_name: str = slugify(name_at_load)
        slug_path: Path = path.with_name(slug_name)
        return cls(local_path=slug_path, _name_at_load=name_at_load)

    @property
    def remotes(self) -> str:
        # FIX: unreadable
        parts: list[str] = [
            f"[white]{self.name}[/]",
            f"[dim]Uploads: {list(self.remote_states.keys())}[/dim]",
        ]
        return " - ".join(parts)

    @property
    def _remotes(self) -> str:
        # MOVE: to silvasta|project.config.setting.Names
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


class CampManager(FileSystemManager):
    def __init__(self):
        config: SachmisConfig = get_config()
        self.role_registry: FileRegistry[SstFile] = FileRegistry(
            local_root=Path(config.paths.role_dir), file_constructor=SstFile
        )
        self.upload_registry: FileRegistry[UploadFile] = FileRegistry(
            local_root=Path(config.paths.camp_dir),
            file_constructor=UploadFile.with_slug_name,
        )

    # def print_loaded(self):
    #     printer.lines_from_list(
    #         lines=[r.description for r in result],
    #         header=f"New loaded files {len(result)}",
    #         title=f"{self.}",
    #     )
