"""
Organize FileTree of Base Directory as Front Side of Forest

"""

from collections import defaultdict
from pathlib import Path
from typing import Self

from loguru import logger
from sstcore import PathGuard
from sstcore.data import FileRegistry, SstFile
from sstcore.utils import FolderScanner, PathTreeNode, ProjectFilter
from sstcore.utils.parse import ParsedName
from sstcore.utils.tree import build_path_tree

from ...config import config
from ...config.models import uniques as model_uniques
from ...config.names import TreeNameSchema
from ...exceptions import SachmisLaunchError

IGNORE_DIRS: set[str] = {".camp"}

ALLOWED_EXTS: set[str] = {".md"}


def plot():  # TASK: customize tree plot
    _tree: PathTreeNode = build_path_tree(paths=[], root_name="name")


# TODO: _create_local_file() will most likely fail?
# - new FrontFile file tracker
# - or derive from SstFileRegistry
class FrontFileRegistry(FileRegistry[SstFile]):
    tree_parser: ParsedName
    prompt_parser: ParsedName
    response_parser: ParsedName
    scanner: FolderScanner
    _sync_mode: PathGuard.SyncMode = PathGuard.SyncMode.OVERRIDE

    def get_trees(self):
        self.get_files_by_keyword("Tree")

    def get_sprouts(self):
        self.get_files_by_keyword({"Prompt", "Response"})

    def get_prompts(self):
        self.get_files_by_keyword({"Prompt"})

    def get_responses(self):
        self.get_files_by_keyword({"Response"})

    def find_tree_above(
        self, path: Path | None = None
    ) -> TreeNameSchema | None:
        # IDEA: just use relative_path.part[0]?
        for part in (path or Path.cwd()).parts:
            if tree_schema := config().names.tree_schema_safe(part):
                return tree_schema

    def all_keywords(self) -> set[str]:
        united_keywords: set[str] = set()
        for file in self.files:
            united_keywords |= file.keywords
        return united_keywords

    def get_tree_id_above(self, path: Path | None = None) -> int:
        if tree_schema := self.find_tree_above(path):
            return tree_schema.tree_id
        raise SachmisLaunchError("Invalid Location, Sprout has not Tree!")

    def get_model_at_path(self, path: Path | None = None) -> set[str]:
        parent_dir: Path = path or Path.cwd()

        all_models: set[str] = model_uniques()
        local_models: set[str] = set()

        for file in self.get_files_by_parent(parent_dir):
            if model := file.keywords & all_models:
                local_models.add(model.pop())

        logger.info(f"Found {len(local_models)} Models in CWD")
        return local_models

    def get_sprout_groups(
        self, path: Path | None = None
    ) -> dict[str, list[SstFile]]:
        """Group all Files at Location by sprout_id"""

        united_keywords: set[str] = set()
        shared_keywords: set[str] = self.all_keywords()
        sprout_groups: dict[str, list[SstFile]] = defaultdict(list)

        for file in self.get_files_by_parent(path):
            united_keywords |= file.keywords
            shared_keywords &= file.keywords
            sprout_id: str = config().names.id_keyword(
                file.local_path, strict=False
            )
            sprout_groups[sprout_id].append(file)

        return sprout_groups

    @classmethod
    def ready(cls) -> Self:
        """Prepare tools, load Registry, scan Forest and be Ready!"""
        logger.info(
            "Loading ProjectFilter, FolderScanner and OutputFileRegistry!"
        )
        # PARAM: default filter stuff, maybe to config.defaults?
        filter = ProjectFilter(exclude={".camp"}, require_any={".md"})
        scanner = FolderScanner(
            scan_root=config().paths.base_dir, filter=filter
        )
        output_files: Self = cls(
            local_root=config().paths.base_dir,
            scanner=scanner,
            tree_parser=config().names.tree_parser,
            prompt_parser=config().names.prompt_parser,
            response_parser=config().names.response_parser,
        )
        output_files.analyze_output_file_status(attach=True)
        output_files.tree()

        return output_files

    def analyze_output_file_status(
        self, attach=True, clear=True
    ) -> list[SstFile]:
        """Select from yielded Paths with Pattern and attach Files"""

        if clear and self.files:
            logger.debug(f"removing {self.n_files} files from registry")
            self.files.clear()

        new_files: list[SstFile] = []

        for path in self.scanner.walk():
            if tree_file := self._extract_if_path_is_tree(path):
                new_files.append(tree_file)

            if prompt_file := self._extract_if_path_is_prompt(path):
                new_files.append(prompt_file)

            if response_file := self._extract_if_path_is_response(path):
                new_files.append(response_file)

        if attach and (n := len(new_files)):
            for file in new_files:
                self.attach(file)
            logger.info(f"Attached {n} Files to OutputFileRegistry")

        return new_files

    def _extract_if_path_is_tree(self, path) -> SstFile | None:
        if schema := config().names.tree_schema_safe(path.name):
            return self._create_sst_file(path, schema.keywords())

    def _extract_if_path_is_prompt(self, path) -> SstFile | None:
        if schema := config().names.prompt_schema_safe(path.name):
            sprout_info: set[str] = self._from_sprout_to_tree(path)
            return self._create_sst_file(path, sprout_info | schema.keywords())

    def _extract_if_path_is_response(self, path) -> SstFile | None:
        if schema := config().names.response_schema_safe(path.name):
            sprout_info: set[str] = self._from_sprout_to_tree(path)
            return self._create_sst_file(path, sprout_info | schema.keywords())

    def _create_sst_file(self, path: Path, keywords: set[str]) -> SstFile:
        relative: Path = PathGuard.relative(path, self.local_root)
        return SstFile(local_path=relative, keywords=keywords)

    def _from_sprout_to_tree(self, path: Path) -> set[str]:

        keywords: set[str] = set()

        for level, part in enumerate(path.parents, start=1):
            if prompt_schema := config().names.prompt_schema_safe(part):
                keywords.add(f"P{level}_{prompt_schema.id_keyword}")  # PARAM:

            if tree_schema := config().names.tree_schema_safe(part):
                keywords.add(tree_schema.id_keyword)
                keywords.add(f"L{level}")
                return keywords

        raise SachmisLaunchError("Invalid Location, Sprout has not Tree!")
