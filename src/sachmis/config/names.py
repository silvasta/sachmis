from contextlib import suppress
from functools import cached_property
from pathlib import Path
from typing import Literal

from loguru import logger
from pydantic import BaseModel, ValidationError
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
    camp_dir: str = "iret"
    # camp_dir: str = "IretCamp"
    hidden_dir: str = ".oasis"
    tree_dir: str = "Trees"
    file_dir: str = "Files"
    image_dir: str = "Images"

    # File system - rollout
    prompt: str = "prompt.md"

    # Patterns
    tree_pattern: str = "t_{tree_id}_{topic}"
    prompt_pattern: str = "p_{sprout_id}_{topic}"
    response_pattern: str = "r_{sprout_id}_{model}_{topic}"

    def id_keyword(self, name: str | Path, strict=True) -> str:
        """Get id plus category from Prompt, Response or Tree"""
        # REMOVE: or combine with below
        if tree_schema := self.tree_schema_safe(name):
            return tree_schema.id_keyword
        if sprout_schema := self.prompt_schema_safe(name):
            return sprout_schema.id_keyword
        if sprout_schema := self.response_schema_safe(name):
            return sprout_schema.id_keyword
        if not strict:
            return "FAIL"
        else:
            raise ValueError(f"id_keyword parsing failed, unknown: {name=}")

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

    def tree_schema_safe(self, name: str | Path) -> TreeNameSchema | None:
        with suppress(ValueError, ValidationError):
            return self.tree_schema(name)

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

    def prompt_schema_safe(self, name: str | Path) -> PromptNameSchema | None:
        with suppress(ValueError, ValidationError):
            return self.prompt_schema(name)

    @cached_property
    def response_parser(self) -> ParsedName:
        return ParsedName[ResponseNameSchema](
            pattern=self.response_pattern,
            model_cls=ResponseNameSchema,
            strip_extension=True,
        )

    def response_stem(self, id: int, model: str, topic: str) -> str:
        return self.response_parser((id, model, topic))

    def response_schema(self, name: str | Path) -> ResponseNameSchema | None:
        return self.response_parser(name)

    def response_schema_safe(
        self, name: str | Path
    ) -> ResponseNameSchema | None:
        with suppress(ValueError, ValidationError):
            return self.response_schema(name)


class NameSchema(BaseModel):
    topic: str

    @property
    def id_keyword(self) -> str:
        parser: ParsedName[IdKeywordSchema] = id_keyword_parser()
        # f"{self._category}_id_{self._id}"
        return parser((self._category, self._id))

    @property
    def _category(self):
        raise NotImplementedError

    @property
    def _id(self):
        raise NotImplementedError

    @property
    def _cls(self):
        raise NotImplementedError

    @property
    def _extra(self) -> set[str]:
        return set()

    def keywords(self) -> set[str]:
        return {self.id_keyword, self._cls} | self._extra


class TreeNameSchema(NameSchema):
    tree_id: int

    @property
    def _category(self):
        return "tree"

    @property
    def _cls(self):
        return "Tree"

    @property
    def _id(self):
        return self.tree_id


class SproutNameSchema(NameSchema):
    sprout_id: int

    @property
    def _category(self):
        return "sprout"

    @property
    def _id(self):
        return self.sprout_id


class PromptNameSchema(SproutNameSchema):
    @property
    def _cls(self):
        return "Prompt"


class ResponseNameSchema(SproutNameSchema):
    model: str

    @property
    def _cls(self):
        return "Response"

    @property
    def _extra(self) -> set[str]:
        return {self.model}


class IdKeywordSchema(BaseModel):
    category: str
    cat_id: int


def id_keyword_parser() -> ParsedName:
    return ParsedName[IdKeywordSchema](
        pattern="{category}_id_{cat_id}",  # PARAM:
        model_cls=IdKeywordSchema,
        strip_increments=False,  # needed to avoid strip id!
    )


def id_keywords_backwards(
    target: Literal["sprout", "tree"], keywords: set[str]
) -> int:
    parser: ParsedName[IdKeywordSchema] = id_keyword_parser()

    for keyword in keywords:
        try:
            schema: IdKeywordSchema = parser(keyword)
            if schema and schema.category == target:
                return schema.cat_id
        except ValidationError, ValueError:
            continue

    logger.error(f"id_keywords_backwards: {target=}, {keywords=}")

    raise ValueError("Failed to Parse!")
