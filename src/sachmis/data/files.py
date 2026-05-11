import uuid
from dataclasses import asdict, dataclass
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
from sstcore.utils import SimpleTreeNode

from sachmis.exceptions import SachmisDataError

from ..config import SachmisConfig, get_config
from ..utils.print import printer


class ConversationTreeNode(SimpleTreeNode):
    pass


@dataclass
class TreeNodeArgs:
    name: str
    id: str


class Conversation(BaseModel):  # TODO: better name
    unique_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    local_id: int  # -1 for not set, starting at 1, for Prompt: 0 == root

    topic: str
    content: str

    @property
    def tree_node_args(self) -> TreeNodeArgs:
        return TreeNodeArgs(name=self._compose_stem(), id=self.unique_id)

    @property
    def tree_node_dict(self) -> dict:
        return asdict(self.tree_node_args)

    def get_ancestor(
        self, unique_id: str | None = None
    ) -> Conversation | None:
        """Direct ancestor, id for Prompt that answers on multiple Responses,
        Response has always 1, Prompt: None -> root, 1 regular, multiple: use id!"""
        if (ancestor := self._get_ancestor()) is None:
            return None
        if isinstance(ancestor, tuple):
            for father in ancestor:
                if father.unique_id == unique_id:
                    ancestor: Conversation = father
                    break
            else:
                raise SachmisDataError(f"{self.desc}: Invalid {unique_id=}")
        self._check_if_class_swiched(ancestor)
        return ancestor

    def as_tree_node(
        self, branches: list[ConversationTreeNode] | None = None
    ) -> ConversationTreeNode:
        if branches is None:
            branches: list[ConversationTreeNode] = []
        return ConversationTreeNode(**self.tree_node_dict, branches=branches)

    def _get_ancestor(self) -> Conversation | tuple[Conversation] | None:
        raise NotImplementedError

    def _check_if_class_swiched(self, other: Conversation):
        """Prompt -> Response -> Pro... required"""
        if isinstance(other, own_class := self.__class__):
            own_cls: str = own_class.__name__
            raise SachmisDataError(f"{own_cls=} directly linke to {own_cls}")

    def get_successor(self) -> list[Conversation]:
        """Direct ancestors, Prompt must have tuple with minimum 1 element,
        Response is growing list that can be empty"""
        for successor in (successors := self._get_successor()):
            self._check_if_class_swiched(successor)
        return successors

    def find_successor(self, unique_id: str) -> Conversation | None:
        for successor in self.get_successor():
            if successor.unique_id == unique_id:
                return successor

    def _get_successor(self) -> list[Conversation]:
        raise NotImplementedError

    def single_ancestor(self) -> Conversation | None:
        raise NotImplementedError

    @property
    def desc(self):
        return f"{self.__class__.__name__} {self.local_id} with {self.topic=}"

    @property
    def slug_topic(self):  # MOVE: Model validate?
        return slugify(self.topic)

    @property
    def stem(self) -> str:
        if self.local_id == -1:
            logger.error("Access to stem without valid local_id")
        return self._compose_stem()

    def _compose_stem(self):
        raise NotImplementedError

    def write(self, root_dir: Path | None = None) -> Path:
        """Rollout to FileSystem"""
        if self.local_id == -1:
            raise SachmisDataError("Write requires assigned local_id!")
        path: Path = self.rollout_path(root_dir)
        path.write_text(self.content)
        logger.info(f"{self.__class__.__name__} wrote to: {path=}")
        return path

    def rollout_path(self, root_dir: Path | None = None) -> Path:
        raise NotImplementedError


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


class CampManager(FileSystemManager):
    """Manage local utilities that are not covered by the Forest"""

    roles: SstFileRegistry  # TODO: Role(SstFile) with content and counter
    files: UploadRegistry
    # TASK: code: (dict or list of) hardlink registry/ies
    images: SstFileRegistry

    def __init__(
        self,
        roles: SstFileRegistry | None = None,
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
        # LATER: combine with global roles, so far unused!
        # - add some tracking of role performance
        self.roles: SstFileRegistry = roles or SstFileRegistry(
            local_root=Path(config.paths.camp_role_dir)
        )
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
