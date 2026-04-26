from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Literal, Self

from boltons.strutils import slugify
from loguru import logger
from pydantic import BaseModel, Field
from sstcore.data import (
    FileRegistry,
    FileSystemManager,
    SstFile,
    SstFileRegistry,
)

from ..config import SachmisConfig, get_config
from ..utils.print import printer


class UploadState(BaseModel):
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
    XaiUploadState | GoogleUploadState,
    Field(discriminator="target"),
]


class UploadFile(SstFile):
    """Local file for upload and usage in prompt"""

    remote_states: dict[str, RemoteState] = Field(default_factory=dict)

    name_at_load: str = Field(default_factory=lambda path: path.name)

    @classmethod
    def with_slug_name(cls, local_path: Path) -> Self:
        name_at_load: str = local_path.name
        slug_name: str = slugify(name_at_load)
        slug_path: Path = local_path.with_name(slug_name)
        return cls(local_path=slug_path, name_at_load=name_at_load)

    @property
    def remotes(self) -> str:
        config: SachmisConfig = get_config()
        return config.names.remotes.styled([self.name, self._remotes])

    def _remotes(self) -> str:
        return " - ".join(list(self.remote_states.keys()))

    @property
    def remotes_plain(self) -> str:
        config: SachmisConfig = get_config()
        return config.names.remotes([self.name, self._remotes])

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
            logger.warning(f"{self.remotes_plain}")
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


class UploadRegistry(FileRegistry[UploadFile]):
    """Registry specifically for UploadFiles"""

    def _create_local_file(self, path: Path) -> UploadFile:
        if path.is_absolute():
            path: Path = self.relative_to_local_root(path)

        return UploadFile.with_slug_name(local_path=path)


class CampManager(FileSystemManager):
    def __init__(self):
        config: SachmisConfig = get_config()

        # TASK: how to handle / sync with Forest?

        # LATER: combine with global roles
        self.role_registry: SstFileRegistry = SstFileRegistry(
            local_root=Path(config.paths.camp_role_dir)
        )
        self.upload_registry: UploadRegistry = UploadRegistry(
            local_root=Path(config.paths.file_dir),
        )
        self.image_registry: SstFileRegistry = SstFileRegistry(
            local_root=Path(config.paths.image_dir),
        )
        logger.info("setup complete")

    def load_files(self, root_dir: Path):
        pass

    def attach_from_camp_folder(self) -> list[UploadFile]:

        # TODO: decide if print here or return here

        new_files: list[UploadFile] = (
            self.upload_registry.attach_new_files_from_local_folder()
        )
        printer.lines_with_len(
            name="New Files",
            lines=[file.description for file in new_files],
        )
        return new_files

    def attach_from_dir(self, local_dir: Path) -> list[UploadFile]:
        """Setup new registry at directory, sync content by config"""

        temp_registry: UploadRegistry = UploadRegistry(local_root=local_dir)
        temp_registry.attach_new_files_from_local_folder()

        logger.debug(f"loaded {temp_registry.n_files} from: {local_dir}")

        return self.registry_sync(
            source=temp_registry,
            target=self.upload_registry,
        )
