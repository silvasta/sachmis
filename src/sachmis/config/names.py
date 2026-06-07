from functools import cached_property
from pathlib import Path

from pydantic import BaseModel
from sstcore.config import SstNames
from sstcore.utils.parse import ParsedName


class Names(SstNames):
    project: str = "sachmis"

    # Global file system - Home / Biome
    setting_file: str = "sachmis_config.json"
    biome_file: str = "biome.json"
    response_dir: str = "full_response"

    # Global and Local
    role_dir: str = "Roles"

    # Local file system - Base / Forest
    forest_file: str = "forest.json"
    base_dir: str = "base"
    camp_dir: str = ".camp"
    tree_dir: str = "Trees"
    file_dir: str = "Files"
    image_dir: str = "Images"

    # File system - rollout
    prompt: str = "prompt.md"

    # Patterns
    tree_pattern: str = "t_{tree_id}_{topic}"
    prompt_pattern: str = "p_{sprout_id}_{topic}"
    response_pattern: str = "r_{sprout_id}_{model}_{topic}"

    @cached_property
    def tree_parser(self) -> ParsedName:
        return ParsedName[TreeNameSchema](
            pattern=self.tree_pattern,
            model_cls=TreeNameSchema,
            strip_extension=True,
        )

    def tree_stem(self, id: int, topic: str) -> str:
        return self.tree_parser((id, topic))

    def tree_schema(self, name: str | Path) -> TreeNameSchema:
        return self.tree_parser(name)

    def tree_id(self, name: str | Path) -> int:
        return self.tree_parser(name).id

    def tree_topic(self, name: str | Path) -> str:
        return self.tree_parser(name).topic

    @cached_property
    def prompt_parser(self) -> ParsedName:
        return ParsedName[PromptNameSchema](
            pattern=self.prompt_pattern,
            model_cls=PromptNameSchema,
            strip_extension=True,
        )

    def prompt_stem(self, id: int, topic: str) -> str:
        return self.prompt_parser((id, topic))

    def prompt_schema(self, name: str | Path) -> PromptNameSchema:
        return self.prompt_parser(name)

    @cached_property
    def response_parser(self) -> ParsedName:
        return ParsedName[ResponseNameSchema](
            pattern=self.response_pattern,
            model_cls=ResponseNameSchema,
            strip_extension=True,
        )

    def response_stem(self, id: int, model: str, topic: str) -> str:
        return self.response_parser((id, model, topic))

    def response_schema(self, name: str | Path) -> ResponseNameSchema:
        return self.response_parser(name)


class TreeNameSchema(BaseModel):
    tree_id: int
    topic: str


class PromptNameSchema(BaseModel):
    sprout_id: int
    topic: str


class ResponseNameSchema(BaseModel):
    sprout_id: int
    model: str
    topic: str
