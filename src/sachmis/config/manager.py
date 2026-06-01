from loguru import logger
from sstcore.config import ConfigManager
from sstcore.utils.path import find_project_root

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
            # FIX: setting_file override
            setting_file=find_project_root() / "configs" / "setting_file.json",
        )

        logger.info("ConfigManager setup completed")
        logger.error(f"Modified: {_config_instance.setting_file=}")

    return _config_instance
