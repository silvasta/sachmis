from loguru import logger
from sstcore.cli import SafeTyper

from ...utils.print import printer
from .biome import (  # import from original exectuion
    Biome,
    BiomeExecutor,
    _load,
    print_all_biome_files,
)


def main() -> None:
    app()


app = SafeTyper(name="debug", help="execute helper or print tests")


@app.command("arbo")
def show_arbo_view_result():
    """Show all Biomes and load active Biome"""
    executor = BiomeExecutor()
    biome: Biome = executor.execute(_load)

    printer.title("Print formated")
    printer(f"{biome}")

    printer.title("Print formated=")
    printer(f"{biome=}")

    printer.title("Print bare")
    printer(biome)
    if hasattr(biome, "stat"):
        printer(biome.stat)

    logger.info(f"Biome Loaded {biome.n_forest=}, {biome.n_responses=}")
    # TASK: replace by stat, move to ArboView
    logger.info(f"Loaded {biome.n_forest=}, {biome.n_responses=}")

    print_all_biome_files()


@app.command("log")
def logger_test():
    logger.debug("ddd")
    logger.info("ddd")
    logger.warning("ddd")
    logger.error("ddd")
    logger.success("ddd")


if __name__ == "__main__":
    main()
