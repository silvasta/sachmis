import json
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
from sstcore.utils.parse import StyledName

from ..config import SachmisConfig, get_config
from ..exceptions import SachmisDataError
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

# MOVE: back to names after setting up style strategy
remotes: StyledName = StyledName.parse_style(
    style_pattern="[{style1}]{name}[/] Remotes: [{style2}]{remotes}[/]",
    keys=["name", "remotes"],
    styles=["blue", "green"],
)


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
        return remotes.styled([self.name, self._remotes])

    def _remotes(self) -> str:
        return " - ".join(list(self.remote_states.keys()))

    @property
    def remotes_plain(self) -> str:
        return remotes([self.name, self._remotes])

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
        return UploadFile.with_slug_name(local_path=local_path)


class Role(SstFile):
    path: Path
    content: str
    rating: float = Field(default=5, ge=0, le=10)

    @classmethod
    def load(cls, path: Path) -> Self:
        return cls.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def save(self, json_path: Path | None = None):
        self.json_file(json_path).write_text(self.to_json(), encoding="utf-8")

    def to_json(self) -> str:
        return self.model_dump_json(exclude_defaults=False, indent=2)

    def json_file(self, path: Path | None = None) -> Path:
        if path and path.suffix == ".json":
            return path
        return self.path.with_suffix(".json")

    @classmethod
    def read(cls, path: Path) -> Self:
        return cls(path=path, local_path=path, content=path.read_text())

    def write(self, txt_path: Path | None = None):
        self.txt_file(txt_path).write_text(self.content)

    def txt_file(self, path: Path | None = None) -> Path:
        if path and path.suffix == ".txt":
            return path
        return self.path.with_suffix(".txt")


class RoleRegistry(FileRegistry[Role]):
    """Registry specifically for Roles"""

    def _create_local_file(self, path: Path) -> Role:
        match path.suffix:
            case ".txt":
                return Role.read(path)
            case ".json":
                return Role.load(path)
            case _:
                if path.exists():
                    raise SachmisDataError(f"Invalid suffix for Role: {path=}")
        raise SachmisDataError(f"Path doesn't exist for Role: {path=}")


class CampManager(FileSystemManager):
    """Manage local utilities that are not covered by the Forest"""

    # TASK: hardlink registry for git-like Code Trees

    roles: RoleRegistry
    files: UploadRegistry
    images: SstFileRegistry

    def __init__(
        self,
        roles: RoleRegistry | None = None,
        files: UploadRegistry | None = None,
        images: SstFileRegistry | None = None,
    ):
        config: SachmisConfig = get_config()

        # TASK: how to handle / sync with Forest?

        self.files: UploadRegistry = files or UploadRegistry(
            local_root=Path(config.paths.file_dir),
        )
        self.images: SstFileRegistry = images or SstFileRegistry(
            local_root=Path(config.paths.image_dir),
        )
        self.roles: RoleRegistry = roles or RoleRegistry(
            local_root=Path(config.paths.camp_role_dir)
            # LATER: add tracking of role performance
        )
        new_roles: list[Role] = self.mirror_roles(paths=config.paths.role_dir)
        printer.lines_with_len("New Roles", lines=new_roles)

        logger.info("setup complete")

    def attach_from_camp_folder(self) -> list[UploadFile]:

        new_files: list[UploadFile] = (
            self.files.attach_new_files_from_local_folder()
        )
        printer.lines_with_len(  # MOVE: to CLI
            name="New Files",
            lines=[file.description for file in new_files],
        )
        logger.error("Move to CLI!!!!")

        return new_files

    def absorb_files(self, paths: Path | list[Path]) -> list[UploadFile]:
        """Move files at path location into camp and registry"""
        return self.files.absorb_from_path(paths)

    def mirror_files(self, paths: Path | list[Path]) -> list[UploadFile]:
        """Copy files at path location into camp and registry"""
        return self.files.mirror_from_path(paths)

    def absorb_images(self, paths: Path | list[Path]) -> list[SstFile]:
        """Move images at path location into camp and registry"""
        return self.images.absorb_from_path(paths)

    def mirror_images(self, paths: Path | list[Path]) -> list[SstFile]:
        """Copy images at path location into camp and registry"""
        return self.images.mirror_from_path(paths)

    def mirror_roles(self, paths: Path | list[Path]) -> list[Role]:
        """Copy images at path location into camp and registry"""
        return self.roles.mirror_from_path(paths)

    def load_files(self, files: list[UploadFile], ensure_after_upload=True):
        """Assumes valid local data files, pushes to Remotes"""
        # TODO: files

        logger.debug("attaching files to data.prompt")

        prompt_files: list[UploadFile] = self.prompt.files

        for file, uploader in product(files, self._uploader.values()):
            try:
                uploader.upload_local_file(file, ensure_after_upload)
                prompt_files.append(file)
            except FileNotFoundError:
                logger.error(f"Missing {file=}")
            except RuntimeError as err:
                logger.error(f"Upload failed {file=}, {err}")
                # TODO: check if raise or not

    def load_images(self, images: list[SstFile]):
        """Assumes valid local image files, pushes to Remotes"""
        # TODO: images
        logger.debug("attaching files to data.image")
        prompt_files: list[SstFile] = self.prompt.images
        prompt_files.extend(images)

    def load_role(self, role_path: Path | None = None):
        if role_path is not None and (role := role_path.read_text()):
            self._role_path: Path | None = role_path
            self._role: str | None = role
