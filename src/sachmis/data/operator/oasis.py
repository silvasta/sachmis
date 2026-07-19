from pathlib import Path

from loguru import logger
from sstcore.data import SstFile, SstFileRegistry
from sstcore.utils import PathFilter

from ...config import config
from ...exceptions import DataRuntimeError
from ..files import Role, RoleRegistry, UploadFile, UploadRegistry


class CampManager:
    """Manage local utilities that are not covered by the Forest"""

    roles: RoleRegistry
    files: UploadRegistry
    images: SstFileRegistry

    def __init__(
        self,
        roles: RoleRegistry | None = None,
        files: UploadRegistry | None = None,
        images: SstFileRegistry | None = None,
    ):

        # Files Setup
        self.files = files or UploadRegistry(
            local_root=Path(config().paths.file_dir)
        )
        if not hasattr(self.files, "scanner") or self.files.scanner is None:
            self.files.setup_scanner(PathFilter())

        # Images Setup
        self.images = images or SstFileRegistry(
            local_root=Path(config().paths.image_dir)
        )
        if not hasattr(self.images, "scanner") or self.images.scanner is None:
            self.images.setup_scanner(PathFilter())

        # Roles Setup
        self.roles = roles or RoleRegistry(
            local_root=Path(config().paths.camp_role_dir)
        )
        if not hasattr(self.roles, "scanner") or self.roles.scanner is None:
            self.roles.setup_scanner(PathFilter())

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

    def prepare_and_load(self, files: list[Path] | None) -> list[UploadFile]:
        # LATER: integrate pick here?
        # - probably not the pick but the match and load after pick

        prepared_files: list[UploadFile] = []

        if files:  # Mirror = copy for CLI provided links
            prepared_files.extend(self.files.mirror_from_path(source=files))

        local_files: Path = config().paths.local_file_dir

        if local_files.exists():
            prepared_files.extend(self.files.absorb_from_path(local_files))

        for file in prepared_files:
            if not file.confirm_local_status(self.files.local_root):
                raise DataRuntimeError(f"Failed to Import {file=}")

        return prepared_files
