from boltons.strutils import slugify
from pydantic import Field
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

    # File system - files
    prompt: str = "prompt.md"


class Defaults(BaseDefaults):
    dot_env_content: str = """# Fill at least 1, delete others
XAI_API_KEY=
GEMINI_API_KEY=
"""


class ProjectSettings(Settings):
    names: Names = Field(default_factory=Names)
    defaults: Defaults = Field(default_factory=Defaults)


def tree_stem(topic: str = "", characteristic: str = "") -> str:
    """Assemble file (or folder) name"""
    # MOVE: attach to Names or create: class Config(ConfigManager)
    topic: str = slugify(topic, delim="-")
    return "_".join(
        [
            name_part
            for name_part in [
                str(day_count()),
                topic,
                characteristic,
            ]
            if name_part != ""
        ]
    )
