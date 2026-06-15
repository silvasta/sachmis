from loguru import logger
from sstcore.cli.engine import SafeTyper

from sachmis.config import SachmisConfig, get_config
from sachmis.exceptions import (
    ArborealFileError,
    SachmisDataError,
    SachmisLaunchError,
)

config: SachmisConfig = get_config()


def main():
    app()


app = SafeTyper(
    name="hello",
    help="CLI for direct communication with LLMs",
    param=config.setup_info,
)


@app.command("v")
def test_value():
    try:
        raise ValueError("fail")
    except ValueError as e:
        logger.error(f"{type(e)}")
        logger.error(f"{e.args}")


@app.command("a")
def test_arbo():
    try:
        raise ArborealFileError("fail")
    except ArborealFileError as e:
        logger.error(e)
        logger.error(f"{type(e)}")


@app.command("l")
def test_launch():
    try:
        raise SachmisLaunchError
    except SachmisLaunchError as e:
        logger.error(f"{type(e)}")
        logger.error(f"{e}")

    try:
        raise SachmisDataError
    except SachmisDataError as e:
        logger.error(e)
        logger.error(f"{e}")


if __name__ == "__main__":
    main()
