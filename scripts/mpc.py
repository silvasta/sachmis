from pathlib import Path

from loguru import logger

from sakhmat.core.data import DataManager
from sakhmat.core.executor import launch_models
from sakhmat.core.forest import File
from sakhmat.core.gemini import Gemini
from sakhmat.core.grok import Grok
from sakhmat.core.model import Model
from sakhmat.core.models import Geminis, Groks
from sakhmat.utils.log import setup_logging
from sakhmat.utils.print import printer

topics = [
    # "bonus-exercises",
    # "introduction",
    # "robust-mpc",
    # "stochastic-mpc",
    # "nonlinear-mpc",
    # "parameter-estimation-learning-based-mpc",
    # "safety-filters",
    # "iterative-learning-based-and-approximate-mpc",
]


def thunder():
    # Log setup
    quiet = False
    log_level = "DEBUG"
    setup_logging(log_level_override=log_level, quiet=quiet)

    # Data setup
    data: DataManager = DataManager()
    data.load_forest()

    # Prompt
    printer.title("Prompt", style="bold white on blue")
    data.load_prompt()
    printer.md(data.prompt)

    # Role
    role = """You are an expert in Model Predictive Control and know the relevant topics,
    for summaries and exams but also for real word application,
    and you have the ability to structure this knowledge in compact form"""
    data.system_role: str = role
    logger.info(f"{role=}")

    # Files
    printer.title("Files", style="bold white on blue")
    data.files: list[File] = data.forest.file_selection(
        topics=topics,
    )
    for file in data.files:
        printer.print(file.description)

    # Images
    printer.title("Images", style="bold white on blue")
    images: list[Path] = []
    data.prepare_images(images)

    # Models
    printer.title("Models", style="bold white on blue")
    models: list[Model] = [
        # Grok(data, Groks.G4FR),
        Grok(data, Groks.G4),
        Gemini(data, Geminis.G3F),
    ]

    # Fire
    DRYRUN = True
    DRYRUN = False
    printer.thunder(f"Launching {data.topic}")
    launch_models(data, models, DRYRUN)


if __name__ == "__main__":
    thunder()
