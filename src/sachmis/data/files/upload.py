"""
Handle Local Files (pdf,code,any..) for Upload

- (Upload->Remote)State: Collect and apply Identifier at Upload or Usage

- UploadFile: Track local file and remote state over time

"""

__all__: list[str] = [
    "UploadState",
    "XaiUploadState",
    "GoogleUploadState",
    "RemoteState",
    "UploadFile",
]

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Literal

from loguru import logger
from pydantic import BaseModel, Field
from sstcore.data import FileRegistry, SstFile

type RemoteState = Annotated[
    XaiUploadState | GoogleUploadState, Field(discriminator="target")
]


class UploadState(BaseModel):
    last_upload: datetime = Field(default_factory=lambda: datetime.now(UTC))

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


class UploadFile(SstFile):
    """Local file for upload and usage in prompt"""

    remote_states: dict[str, RemoteState] = Field(default_factory=dict)

    # @classmethod
    # FIX: problem for absorb, path is changed before file is moved to that!
    # - consider absorbing (copy etc) moves from old stem to path with new stem
    # - ATTENTION: use STEM not NAME! otherwise: file_tex

    # stem_at_load: str = Field(default_factory=lambda path: path.stem)
    #
    # def with_slug_name(cls, local_path: Path) -> Self:
    #     stem_at_load: str = local_path.stem
    #     slug_stem: str = slugify(stem_at_load)
    #     slug_path: Path = local_path.with_stem(slug_stem)
    #     return cls(local_path=slug_path, stem_at_load=stem_at_load)

    def attach_remote(self, state: RemoteState):
        """Attach new remote states"""
        self.remote_states[state.target] = state
        self.touch()

    def find_remote(self, target: str) -> RemoteState | None:
        """Find and get remote state for 'target', None for not found"""
        return self.remote_states.get(target)

    def has_remote(self, target: str) -> bool:
        """Check if remote state for 'target' is available"""
        return self.find_remote(target) is not None

    def get_remote_state(self, target: str) -> RemoteState:
        """Get remote state for 'target' or raise"""
        logger.debug(f"extracting for {target=}")
        if (remote_state := self.remote_states.get(target)) is None:
            logger.warning(f"{self.remotes_plain}")
            raise AttributeError(f"No remote state for {target} available!")
        return remote_state

    def remove_remote(self, target: str) -> RemoteState | None:
        """Remove 'target' remote_states, get value or None for not existing"""
        if (remote_state := self.remote_states.pop(target, None)) is None:
            logger.warning(f"Attempt to remove not existing remote: {target=}")
        else:
            self.touch()
            logger.debug(f"removed {target} from remote_states")
        return remote_state


class UploadRegistry(FileRegistry[UploadFile]):
    """Registry specifically for UploadFiles"""

    def _create_local_file(self, local_path: Path) -> UploadFile:
        # FIX: slug
        return UploadFile(local_path=local_path)
