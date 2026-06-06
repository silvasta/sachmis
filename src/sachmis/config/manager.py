from loguru import logger
from sstcore.config import ConfigManager

from .defaults import Defaults
from .names import Names
from .paths import Paths
from .settings import Settings

type SachmisConfig = ConfigManager[Settings, Names, Defaults, Paths]

_config_instance: SachmisConfig | None = None


def get_config() -> SachmisConfig:
    global _config_instance

    if _config_instance is None:
        logger.info("Setup Sachmis ConfigManager...")

        _config_instance = ConfigManager(
            settings_cls=Settings,
            paths_cls=Paths,
            project_name="Sachmis",
        )

        logger.info("ConfigManager setup completed")

    return _config_instance
