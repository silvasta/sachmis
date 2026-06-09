from pathlib import Path

from loguru import logger
from sstcore.data import SstFile, SstFileRegistry

from ..config import SachmisConfig, get_config
from ..utils.print import printer
from .files import Role, RoleRegistry, UploadFile, UploadRegistry


class CampManager:
    """Manage local utilities that are not covered by the Forest"""

    # LATER:
    # TASK: hardlink registry for git-like Code Trees
    # - check sstcore.data.files_todo

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

        # TEST:
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

    def load_role(self, role: Path | None = None) -> Role | None:
        """Great pipeline still in construction"""
        if role is not None:
            if not role.is_file():
                logger.warning(f"Invalid path: {role=}")
            return Role.read(path=role)

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
