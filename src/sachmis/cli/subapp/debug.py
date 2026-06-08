from loguru import logger
from sstcore.cli import SafeTyper


def main() -> None:
    app()


app = SafeTyper(
    name="d",
    help="Forest - Home of every Tree",
)


@app.command("log")
def logger_test():
    logger.debug("ddd")
    logger.info("ddd")
    logger.warning("ddd")
    logger.error("ddd")
    logger.success("ddd")


if __name__ == "__main__":
    main()
