
from loguru import logger
from silvasta.config import ConfigManager

from .paths import Paths
from .settings import Defaults, Names, Settings

type SachmisConfig = ConfigManager[Settings, Names, Defaults, Paths]

_config_instance: SachmisConfig | None = None


def get_config() -> SachmisConfig:
    global _config_instance

    if _config_instance is None:
        logger.info("Setup Sachmis ConfigManager...")

        _config_instance = ConfigManager(
            settings_cls=Settings,
            paths_cls=Paths,
            write_new_master_setting_file_if_missing=True,
        )
        logger.info("ConfigManager setup completed")
    else:
        logger.debug("provide cached config")

    return _config_instance
