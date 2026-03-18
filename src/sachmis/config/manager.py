from loguru import logger
from silvasta.config.manager import ConfigManager

from .settings import Defaults, Names, Paths, ProjectSettings

# TODO: similar config setup as in log
# - create singleton or return already created singleton
# - save configs from CLI input! as in fily-analyzer

config: ConfigManager[
    ProjectSettings,
    Names,
    Defaults,
    Paths,
] = ConfigManager(
    settings_cls=ProjectSettings,
    paths_cls=Paths,
    save_defaults_to_file=True,
)

logger.info("ConfigManager setup completed")
