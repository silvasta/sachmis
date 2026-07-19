from sstcore.config import ConfigManager
from sstcore.config.setup import ConfigLoader, sst_config_loader

from . import models
from .defaults import Defaults
from .names import Names
from .paths import Paths
from .settings import Settings

__all__: list[str] = [
    "SachmisConfig",
    "config_loader",
    "Paths",
    "Settings",
    "Names",
    "Defaults",
    "models",
]


type SachmisConfig = ConfigManager[Settings, Names, Defaults, Paths]


def config_loader() -> ConfigLoader[SachmisConfig]:
    """Prepare loader function ready to setup SachmisConfig"""

    return sst_config_loader(
        settings_cls=Settings,
        paths_cls=Paths,
        project_name="sachmis",
    )
