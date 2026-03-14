from pathlib import Path
from ..core.executor import launch_models, match_family
from ..core.data import DataManager
from loguru import logger
from typing import Annotated

import typer

from ..core.grok import Grok
from ..core.model import Model
from ..core.gemini import Gemini
from ..core.models import Geminis, Groks, Models
from ..utils.log import logger_catch
from ..utils.print import printer

# REMOVE: everything! new concept! probably organized from tui, until then by scripts
file_dir = Path("home/silvan/Grok/latest/data/input-files/uploaded")
xai_files: list[dict[str, Path]] = [
    {
        "file_ded964d1-9391-4a2f-aebc-110316e70056": file_dir / "AML_25_RL_quiz.pdf",
    },
    # Lecture
    {
        "file_1c19b845-9f86-412a-a707-aed34b78e57e": file_dir
        / "AML-L10-rl-and-active-learning_active-learning-slides.pdf",
        "file_89ddab62-72a8-4269-b9b6-5ba45ab2be65": file_dir
        / "AML-L10-rl-and-active-learning_annotated-slides-rl.pdf",
        "file_97cf0621-a858-4f59-a83f-231a192e96f0": file_dir
        / "AML-L10-rl-and-active-learning_rl-slides.pdf",
    },
    # Exercise
    {
        "file_7e2b00d7-a111-404d-93f9-5c951c24006c": file_dir
        / "group1_exercise_w1.pdf",
        "file_5c0065c0-6066-4c8c-a683-441013d238ec": file_dir
        / "group1_exercise_w1_sol.pdf",
        "file_1d17cae2-6f01-4238-b916-499518069857": file_dir
        / "group1_exercise_w2.pdf",
        "file_5ff85eb3-39f8-4032-8bff-c43b7a058cb3": file_dir
        / "group1_exercise_w2_sol.pdf",
    },
    # slides
    {
        "file_d12ddef6-75b8-4c5e-b0d0-82aaad8cdbd0": file_dir / "group1_slides_w1.pdf",
        "file_11bbe5f9-ec8a-4294-b212-4e671987683c": file_dir / "group1_slides_w2.pdf",
        "file_5337b617-cddb-4005-887e-b645247775e1": file_dir / "group2_slides_w1.pdf",
        "file_2f578484-25c2-4bd5-82dc-d796139e6b09": file_dir / "group2_slides_w2.pdf",
    },
    # TEX
    {
        "file_f2fe6204-c26d-426c-ae2c-6a702e285771": file_dir / "summary-1.tex",
        "file_6794c44d-4fbe-4725-9a6c-48b5fdb407d1": file_dir / "summary-2.tex",
        "file_0de4b3b2-20e1-419e-8da0-021959b7a14b": file_dir / "summary-3.tex",
    },
    # EXERCISE
    {
        "file_1e1897d1-55d8-4b7e-aa13-7fee36fc063b": file_dir
        / "week1_in-class_exercises.pdf",
        "file_5b32b507-b1de-4e51-aabc-8e231bd13e3b": file_dir
        / "week1_in-class_exercises_solution.pdf",
        "file_47d50e2e-9abb-43f4-977e-5f210d814808": file_dir
        / "week2_in-class_exercises.pdf",
        "file_22056e27-4372-48db-b9e1-4a824afafac3": file_dir
        / "week2_in-class_exercises_solution.pdf",
    },
]

xai_diffusion: list[dict[str, Path]] = [
    {
        "file_d4ae9e23-46f6-4c86-9ba3-85ebc1bc03c7": file_dir
        / "AML_25_diffusion_quiz.pdf",
    },
    {
        "file_f3765407-4abe-4326-8021-fe5dc7c05d32": file_dir
        / "Diffusion Models -- Lecture Notes.pdf",
    },
    {
        "file_1a932958-2e6a-4a55-9f0e-0eed8522043d": file_dir
        / "g_1_slides_0_Overview.pdf",
        "file_8297cb5e-14ba-4702-8f8b-494b6906ec15": file_dir
        / "g_1_slides_10_Fokker_Planck.pdf",
        "file_3ac2336f-26c9-4627-9c26-8eedea72843c": file_dir
        / "g_1_slides_1_Preliminaries.pdf",
        "file_8cf91de9-b353-44e3-a710-5d0d099c6f76": file_dir
        / "g_1_slides_2_ScoreMatching.pdf",
        "file_e304c43f-cd9e-4abd-aaa6-05d626ccad6b": file_dir
        / "g_1_slides_3_NoiseConditionalScoreMatching.pdf",
        "file_6f42aba1-daf3-4793-9e85-cc4fdb4feb3c": file_dir
        / "g_1_slides_4_LangevinSampling.pdf",
        "file_d2c97f4f-1a5c-4996-901b-9c664f68a333": file_dir / "g_1_slides_5_DDPM.pdf",
        "file_258f542f-47f0-4847-aacc-8e3fb5a52767": file_dir
        / "g_1_slides_6_ContinuousForwardProcess.pdf",
        "file_49b4b904-9cef-4f26-b055-6f2b8a4a916c": file_dir
        / "g_1_slides_7_ItoCalculus.pdf",
        "file_bb57f403-cf31-425e-b432-3b44e6028ac8": file_dir
        / "g_1_slides_8_ForwardSDE_Andersons.pdf",
        "file_f17b5bdb-d51e-4877-ba14-0235c65d3975": file_dir
        / "g_1_slides_9_EulerMaruyama.pdf",
    },
    {
        "file_a818e184-dade-479a-aab3-429c03da79cc": file_dir
        / "g_2_slides_0_Overview.pdf",
        "file_e600d7c0-082e-4760-8c83-ceebf947b45b": file_dir
        / "g_2_slides_1_ItoCalculus.pdf",
        "file_d9aba618-59e7-4c3b-904c-020b6e051b92": file_dir
        / "g_2_slides_2_LangevinDynamics.pdf",
        "file_867bdef4-4f1d-4814-80f5-1bbebc351362": file_dir
        / "g_2_slides_3_EulerMaruyama.pdf",
        "file_deace38a-38dd-4585-8701-3794c8336168": file_dir
        / "g_2_slides_4_UnadjustedLangevinSampling.pdf",
        "file_602c9a3b-45e7-4173-9028-ef1cbe91a160": file_dir
        / "g_2_slides_5_ScoreMatching.pdf",
        "file_5f96638e-b535-45f4-88fa-39e3b63dd469": file_dir
        / "g_2_slides_6_NoiseConditionalScoreMatching.pdf",
        "file_c5b6fd18-e85f-4cd3-8c10-57c16c89fbe9": file_dir
        / "g_2_slides_7_AnnealedLangevinSampling.pdf",
        "file_62cfa0c2-f973-4d3a-b23e-5d39bf6f5dd5": file_dir
        / "g_2_slides_8_ForwardSDE_Andersons.pdf",
        "file_01df7b8f-c08d-42a1-b1a3-3187df772141": file_dir / "g_2_slides_9_DDPM.pdf",
    },
]


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
    printer.thunder("Executing strategic script!")

    data: DataManager = ctx.obj["data"]
    data.load_forest()

    raw_models: list[Models] = [
        Groks.G41FR,
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

    data.xai_files: list[str] = [id for id in file_group for file_group in xai_files]
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
