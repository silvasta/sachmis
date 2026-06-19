from pathlib import Path

from sstcore.config import ConfigManager
from sstcore.config.loader import get_config, sst_config_loader

from .defaults import Defaults
from .names import Names
from .paths import Paths
from .settings import Settings

type SachmisConfig = ConfigManager[Settings, Names, Defaults, Paths]


def config_loader(setting_file: Path | None = None) -> SachmisConfig:
    """Prepare Loader for SachmisConfig"""

    return sst_config_loader(
        settings_cls=Settings,
        paths_cls=Paths,
        setting_file=setting_file,
        project_name="sachmis",
    )


# TEST: usable like this?
def config() -> SachmisConfig:
    """Fetch the initialized Sachmis config"""
    return get_config()
