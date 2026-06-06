from sstcore.config import SstNames, StyledName

# from sstcore.utils import day_count


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
    tree_file: str = "t_{id}_{topic}.json"
    sprout_stem: str = "c_{id}_{spec}_{topic}"

    remotes: StyledName = StyledName.parse_style(
        style_pattern="[{style1}]{name}[/] Remotes: [{style2}]{remotes}[/]",
        keys=["name", "remotes"],
        styles=["blue", "green"],
    )
