from pathlib import Path

from loguru import logger

from sachmis.core.data import DataManager
from sachmis.core.executor import launch_models
from sachmis.core.forest import File
from sachmis.core.gemini import Gemini
from sachmis.core.grok import Grok
from sachmis.core.model import Model
from sachmis.core.models import Geminis, Groks
from sachmis.utils.log import setup_logging
from sachmis.utils.print import printer


def thunder():
    # Log setup
    quiet = False
    # log_level = "DEBUG"
    log_level = "INFO"
    setup_logging(log_level_override=log_level, quiet=quiet)

    # Data setup
    data: DataManager = DataManager()
    data.load_forest()

    # Role
    role = """You are an expert in Robot Dynamics and know the relevant topics,
    for summaries and exams but also for real word application,
    and you have the ability to structure this knowledge in compact form"""
    data.system_role: str = role
    logger.info(f"{role=}")

    topics: list[str] = [
        # "dynamics",
        "General",
        # "fixedwing",
        # "legged",
        # "introduction",
        # "rotorcrafts",
        # "summary2025",
        # "kinematics",
    ]
    categories: list[str] = [
        # "General",
        "Tex",
        # "Exam",
        # "Quiz",
        # "Lecture",
    ]

    for topic in topics:
        # Prompt
        printer.title("Prompt", style="bold white on blue")
        load_from_file = True
        # load_from_file = False
        if load_from_file:
            data.load_prompt()
        else:
            data.load_prompt(prompt_text=create_prompt(topic))
        printer.md(data.prompt)

        # Files
        printer.title("Files", style="bold white on blue")
        # data.files: list[File] = data.forest.file_selection(
        #     # topics=[topic],
        #     categories=categories,
        # )
        tex_files: list[File] = data.forest.file_selection(
            # topics=topics,
            categories=categories,
        )
        for file in tex_files:
            if file.name in ["sst-custom.cls", "rodyn.tex"]:
                data.files.append(file)
        for file in data.files:
            printer.print(file.description)

        # Images
        printer.title("Images", style="bold white on blue")
        images: list[Path] = []
        data.prepare_images(images)

        # Models
        printer.title("Models", style="bold white on blue")
        models: list[Model] = [
            # Grok(data, Groks.G41FR),
            Grok(data, Groks.G4),
            # Gemini(data, Geminis.G3F),
        ]

        # Fire
        DRYRUN = True
        # DRYRUN = False
        printer.thunder(f"Launching {data.topic}")
        launch_models(data, models, DRYRUN)


def create_prompt(topic: str):
    return f""" # Summary for Section {topic}

In the attached files you find the material for the {topic=} to cover in this step.

The idea is to analyze the lecture material, filter the information by relevance for the exam and extract useful hints, formulas and calculus receipts.

The **goal** is to create a section in latex format for the exam formula sheet.
Example `tex` files are attached, the main file and the `cls` and already completed parts of the summary (kinematics and dynamics)

## TASK

- Check the lecture material, especially look for exam relevant stuff
- Summarize all important formulas, tricks and other stuff, formatted in latex and ready to plug-in into the template
"""


if __name__ == "__main__":
    thunder()
