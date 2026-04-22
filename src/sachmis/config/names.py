import re
from typing import Self

from boltons.strutils import slugify
from silvasta.config import ParsedName, SstNames
from silvasta.utils import day_count


class SproutName(ParsedName):
    @classmethod
    def _load_predefined_keys(cls) -> list[str]:
        return [
            "{dom}",
            "{spec}",
            "{locator}",
            "{topic}",
        ]

    def computed(
        self, topic: str = "", locator: str = "", spec: str = ""
    ) -> str:
        values: list[str] = [
            str(day_count()),
            spec,
            locator,
            slugify(topic, delim="-"),
        ]
        return self(values)


class StyledName(ParsedName):
    style_pattern: str
    styles: list[str]

    def styled(self, target: dict | list) -> str:
        rich_template: str = self.style_pattern
        for i, style in enumerate(self.styles, start=1):
            rich_template = rich_template.replace(f"{{style{i}}}", style)

        # MOVE: ParsedName
        target_dict: dict[str, str] = {}

        # MOVE: ParsedName
        if isinstance(target, list):
            for i, key in enumerate(self.keys):
                target_dict[key] = (
                    target[i] if i < len(target) else f"UNKNOWN_{i}"
                )
        # MOVE: ParsedName
        else:
            target_dict = target
        return rich_template.format(**target_dict)

    @classmethod
    def parse_pattern(
        cls, style_pattern: str, keys: list[str], styles: list[str]
    ) -> Self:
        """Use transfromed style_pattern as base pattern for regex parser setup"""

        pattern: str = re.sub(r"\[.*?\]", "", style_pattern)

        return cls(
            pattern=pattern,
            keys=keys,
            style_pattern=style_pattern,
            styles=styles,
        )


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
    tree_dir: str = "Trees"

    # File system - rollout
    prompt: str = "prompt.md"

    # Patterns
    sstfile_dates: StyledName = StyledName.parse_pattern(
        style_pattern="[{style1}]{name}[/]: [{style2}]{first_tracked}[/] - [{style3}]{last_updated}[/]",
        keys=["name", "first_tracked", "last_updated"],
        styles=["blue", "dim", "white"],
    )

    sprout_stem: SproutName = SproutName.with_predefined_keys()
