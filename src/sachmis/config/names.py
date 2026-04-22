from boltons.strutils import slugify
from silvasta.config import SstNames
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
    tree_dir: str = "Trees"

    # File system - rollout
    prompt: str = "prompt.md"

    @staticmethod
    def sprout_stem(topic: str = "", locator: str = "", spec: str = "") -> str:

        # INFO: still under development

        # NEXT: Tree name generator?
        # TODO: handle together with backward parsing
        name_parts: list[str] = [
            str(day_count()),
            spec,
            locator,
            slugify(topic, delim="-"),
        ]
        return "_".join([part for part in name_parts if part])
