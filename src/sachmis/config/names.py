from boltons.strutils import slugify
from sstcore.config import ParsedName, SstNames, StyledName

# from sstcore.utils import day_count


class SproutName(ParsedName):
    @classmethod
    def _load_predefined_keys(cls) -> list[str]:
        return [
            # "dom",
            "locator",
            "spec",
            "topic",
        ]

    # TEST: swap keys, what happens?

    def computed(self, topic: str, locator: str, spec: str) -> str:
        values: list[str] = [
            # str(day_count()),
            locator,
            spec,
            slugify(topic, delim="-"),
        ]
        return self(values)


# REMOVE: ??
# parts: list[str] = [
#     "[{style1}]{name}[/] Remotes: [{style2}]{remotes}[/]",
# ]


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
    tree_file: ParsedName = ParsedName(pattern="t_{id}_{stem}.json")
    sprout_stem: SproutName = SproutName.with_predefined_keys()

    remotes: StyledName = StyledName.parse_style(
        style_pattern="[{style1}]{name}[/] Remotes: [{style2}]{remotes}[/]",
        keys=["name", "remotes"],
        styles=["blue", "green"],
    )
