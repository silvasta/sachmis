"""
Handle Local Files (pdf,code,any..) for Upload

- (Upload->Remote)State: Collect and apply Identifier at Upload or Usage

- UploadFile: Track local file and remote state over time

"""

from sstcore.utils import ColorBox
from sstcore.utils.view.mixin.log import PydanticDataMixin

from sachmis.utils.views import SimpleNameMixin, Status

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

from pydantic import BaseModel, Field
from sstcore.data import FileRegistry, SstFile

type RemoteState = Annotated[
    XaiUploadState | GoogleUploadState, Field(discriminator="target")
]


c = ColorBox()


class _View(SimpleNameMixin, PydanticDataMixin):
    is_valid: bool

    def __rich__(self) -> str:
        return c(self, self._match_status_().color)

    def _match_status_(self) -> Status:
        return Status.CONFIRMED if self.is_valid else Status.CONFLICT
        # status = Status.from_bool()


class UploadState(_View, BaseModel):
    last_upload: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def age(self) -> timedelta:
        """Return time since last upload of file"""
        return datetime.now(UTC) - self.last_upload

    def is_valid(self) -> bool:
        raise NotImplementedError

    @property
    def remote_id(self) -> str:
        raise NotImplementedError


class XaiUploadState(UploadState):
    target: Literal["xai"] = "xai"
    # TODO: maybe filename? (for __print__)
    x_id: str

    def is_valid(self) -> bool:  # LATER: specific checks
        return True

    @property
    def remote_id(self) -> str:
        return self.x_id


class GoogleUploadState(UploadState):
    target: Literal["google"] = "google"

    g_uri: str
    g_mime_type: str
    g_name: str

    @property
    def is_outdated(self) -> bool:
        """Files are deleted after 48 hours"""
        return self.age > timedelta(hours=47)  # PARAM:

    def is_valid(self) -> bool:  # LATER: more specific checks
        return all([self.is_outdated])

    @property
    def remote_id(self) -> str:
        return self.g_uri  # TEST:


class UploadFile(SstFile):
    """Local file for upload and usage in Prompt"""

    remote_states: dict[str, RemoteState] = Field(default_factory=dict)

    def attach_remote(self, state: RemoteState):
        self.remote_states[state.target] = state
        self.touch()

    def find_remote(self, target: str) -> UploadState | None:
        return self.remote_states.get(target)

    def has_remote(self, target: str) -> bool:
        return self.find_remote(target) is not None

    def remove_remote(self, target: str) -> UploadState | None:
        if remote_state := self.remote_states.pop(target, None):
            self.touch()
        return remote_state


class UploadRegistry(FileRegistry[UploadFile]):
    """Registry specifically for UploadFiles"""

    def _create_local_file(self, local_path: Path) -> UploadFile:
        return UploadFile(local_path=local_path)  # FIX: slug
