from loguru import logger
from sstcore.config import ConfigManager

from .defaults import Defaults
from .names import Names
from .paths import Paths
from .settings import Settings

# AI: so far I never made a real derivative class of ConfigManager
# for all others it is like 95% sure that they get derived for the project
# here in Sachmis Settings is just 5 lines, Names and Paths both > 200, Defaults ~100+

type SachmisConfig = ConfigManager[Settings, Names, Defaults, Paths]

_config_instance: SachmisConfig | None = None


def get_config() -> SachmisConfig:
    global _config_instance

    if _config_instance is None:
        logger.info("Setup Sachmis ConfigManager...")
        # AI: so far I was looking for the best spot to intercept the
        # initial logger process (as it is usually a lot of spam for CLI)
        # - maybe if I just interrcept the log to console at init?
        #  (later on I want and i need log to console, after setup is fine)
        logger.remove()  # REMOVE:

        _config_instance = ConfigManager(
            # AI: here get all the information feeded to config
            # - but with that, no control over like a setting file path
            #   or for example the desired (or changed) home setup
            settings_cls=Settings,
            paths_cls=Paths,
            project_name="sachmis",
        )

        logger.info("ConfigManager setup completed")

    return _config_instance
