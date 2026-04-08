from pathlib import Path
from typing import Annotated

import typer
from loguru import logger
from silvasta.cli.setup import logger_catch

from sachmis.config.model import Geminis, Groks, ModelFamily
from sachmis.core.model import Gemini, Grok, Model
from sachmis.data import DataManager
from sachmis.utils.print import printer

# IMPORTANT: launch v0.4.0b1 when this is ready!

# REFACTOR: everything here below
# /41/󰌠 /aml.py
# /42/󰌠 /gtc.py
# /43/󰌠 /mpc.py
# /44/󰌠 /robol-hw1.py
# /45/󰌠 /rodyn.py

# REFACTOR: everything here below


@logger_catch
def thunder(
    ctx: typer.Context,
    # - - - Async - - - #
    use_async: Annotated[
        bool,
        typer.Option(
            "--use-async",
            "-a",
            help="Send all models together with async",
        ),
    ] = True,
    # - - - DRYRUN - - - #
    DRYRUN: Annotated[
        bool,
        typer.Option(
            "--dry",
            help="Just simulate pipeline without online requests",
        ),
    ] = False,
):
    """Release specific assembled task script"""
    printer("Executing strategic script!")

    data: DataManager = ctx.obj["data"]
    data.load_forest()

    raw_models: list[ModelFamily] = [
        Geminis.G3F,
    ]
    logger.debug(f"Using: {raw_models=}")

    images: list[Path] = []
    data.prepare_images(images)
    logger.debug(f"Using: {images=}")

    logger.debug(f"Using: {xai_files=}")

    data.load_prompt()

    speed_reader = "You are an expert in reading and summarizing lecture material about machine learning fast and efficiant"
    data.load_system_role(role_text=speed_reader)
    logger.info(f"{speed_reader=}")

    models: list[Model] = []

    # for file_group in xai_files:
    for file_group in xai_diffusion:
        for id, path in file_group.items():
            data.xai_files: list[str] = [id]
            data.input_file_paths: list[Path] = [path]
            grok = Grok(
                data,
                Groks.G41FR,
                reasoning_effort="high",
                topic=path.stem,
            )
            print("plus grok")

            gemini = Gemini(
                data,
                Geminis.G3F,
                thinking_budget=624,
                topic=path.stem,
            )
            print("plus gem")

            models += [grok, gemini]
            logger.debug(f"Added pair for: {path}")

    overview_reader = "You are an expert in machine learning with an eye on the big picture of a topic"
    data.load_system_role(role_text=overview_reader)
    logger.info(f"{overview_reader=}")

    data.xai_files: list[str] = [
        id for id in file_group for file_group in xai_files
    ]
    models += [
        Grok(
            data,
            Groks.G41FR,
            reasoning_effort="high",
            topic="groot",
        )
    ]

    logger.info(f"{len(models)} in pipeline!")
    printer.thunder(f"{len(models)} Models ready for THUNDER!")
    logger.info(f"{DRYRUN}")

    launch_models(
        data,
        models,
        use_async,
        DRYRUN,
    )
