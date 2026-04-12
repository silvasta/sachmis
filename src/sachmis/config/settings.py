from boltons.strutils import slugify
from pydantic import Field
from pydantic_settings import BaseSettings
from silvasta.config import (
    SstDefaults,
    SstNames,
    SstSettings,
)
from silvasta.utils import day_count


class Names(SstNames):
    project: str = "sachmis"

    # Global file system - Home / Biome
    biome_file: str = "biome.json"
    setting_file: str = "sachmis_config.json"

    # Local file system - Base / Forest
    forest_file: str = "forest.json"
    base_dir: str = "base"
    camp_dir: str = ".camp"
    file_dir: str = "files"
    image_dir: str = "images"

    # File system - files
    prompt: str = "prompt.md"

    @staticmethod
    def sprout_stem(
        topic: str = "", tree_locator: str = "", spec: str = ""
    ) -> str:

        # INFO: still under development

        # TODO: handle together with backward parsing
        name_parts: list[str] = [
            str(day_count()),
            spec,
            tree_locator,
            slugify(topic, delim="-"),
        ]
        return "_".join([part for part in name_parts if part])


class TenacityDefaults(BaseSettings):
    max_attempts: int = 3
    wait_exponential: dict[str, int] = {
        "multiplier": 1,
        # NEXT: check gemini chat, this few seconds are ridicoulous!
        "min": 2,
        "max": 10,
    }


class Defaults(SstDefaults):
    tenacity: TenacityDefaults = Field(default_factory=TenacityDefaults)
    topic: str = "Default Topic"
    dot_env_content: str = """# Fill at least 1, delete others
XAI_API_KEY=
GEMINI_API_KEY=
"""


class Settings(SstSettings):
    names: Names = Field(default_factory=Names)
    defaults: Defaults = Field(default_factory=Defaults)
