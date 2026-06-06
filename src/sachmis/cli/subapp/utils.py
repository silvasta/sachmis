from loguru import logger
from sstcore.cli import SafeTyper, utils_app

from ...config import SachmisConfig, get_config
from ...data import DataManager
from ...utils.print import printer

config: SachmisConfig = get_config()


def main() -> None:
    app()


app: SafeTyper = utils_app


@app.command()
def data(biome: bool = False, forest: bool = False):
    """Open DataManger in Context: with DataManger() as data..."""

    # NEXT:
    with DataManager(biome, forest) as data:
        printer(vars(data))


@app.command("log")
def logger_test():
    logger.debug("ddd")
    logger.info("ddd")
    logger.warning("ddd")
    logger.error("ddd")
    logger.success("ddd")


if __name__ == "__main__":
    main()
