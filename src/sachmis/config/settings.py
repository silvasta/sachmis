from boltons.strutils import slugify
from pydantic import Field
from pydantic_settings import BaseSettings
from silvasta.config.settings import (
    BaseDefaults,
    BaseNames,
    Settings,
)
from silvasta.utils import day_count


class Names(BaseNames):
    new_base_tag: str = "NEW BASE"  # used for log write ans search

    # Global file system - Home / Biome
    biome_file: str = "biome.json"

    # Local file system - Base / Forest
    base_dir: str = "base"
    forest_file: str = "forest.json"
    camp_dir: str = ".camp"
    file_dir: str = "files"
    image_dir: str = "images"

    # File system - files
    prompt: str = "prompt.md"

    @staticmethod
    def tree_stem(topic: str = "", characteristic: str = "") -> str:
        """Assemble file (or folder) name"""

        name_parts: list[str] = [
            str(day_count()),
            slugify(topic, delim="-"),
            characteristic,
        ]
        return "_".join([part for part in name_parts if part])


class TenacityDefaults(BaseSettings):
    max_attempts: int = 3
    wait_exponential: dict[str, int] = {
        "multiplier": 1,
        "min": 2,
        "max": 10,
    }
    # TODO: log retries
    # sleep_log(logger, logging.WARNING)


class Defaults(BaseDefaults):
    tenacity: TenacityDefaults = Field(default_factory=TenacityDefaults)
    topic: str = "Default Topic"
    dot_env_content: str = """# Fill at least 1, delete others
XAI_API_KEY=
GEMINI_API_KEY=
"""


class ProjectSettings(Settings):
    names: Names = Field(default_factory=Names)
    defaults: Defaults = Field(default_factory=Defaults)
