from loguru import logger
from pathlib import Path
from sakhmat.utils.log import setup_logging
from sakhmat.core.model import Model
from sakhmat.core.data import DataManager
from sakhmat.core.executor import launch_models
from sakhmat.core.grok import Grok
from sakhmat.core.gemini import Gemini
from sakhmat.core.models import Groks, Geminis
from sakhmat.core.forest import File
from sakhmat.utils.print import printer


topics: list[str] = [
    "past-exams",
    # "week-1-introduction-and-administrative-information",
    # "week-3-representations-rao-cramer-bound",
    # "week-4-gaussian-processes-and-ensembles",
    # "week-5-svms-and-ensembles",
    # "week-6-neural-networks-attention-and-transformers",
    # "week-7-computer-vision-slides",
    # "week-8-graph-neural-networks-and-information-theory",
    # "week-9-anomaly-detection",
    # "week-10-rl-and-active-learning",
    # "week-11-counterfactual-invariance-and-reproducing-kernel-hilbert-spaces",
    # "week-12-variational-autoencoders-and-non-parametric-bayesian-methods",
    # "weeks-13-and-14-pac-learning",
]


def thunder():
    # Log setup
    quiet = False
    log_level = "DEBUG"
    setup_logging(log_level_override=log_level, quiet=quiet)

    # Data setup
    data: DataManager = DataManager()
    data.load_forest()

    # Role
    role = """You are an expert in Machine Learning!
    You know the relevant topics for summaries and exams,
    and you have the ability to structure this knowledge in compact form"""
    data.system_role: str = role
    logger.info(f"{role=}")

    for topic in topics:
        # Prompt
        printer.title("Prompt", style="bold white on blue")
        criteria = True
        if criteria:
            data.load_prompt()
        else:
            data.load_prompt(prompt_text=create_prompt(topic))
        printer.md(data.prompt)

        # Files
        printer.title("Files", style="bold white on blue")
        data.files: list[File] = data.forest.file_selection(
            topics=[
                topic,
                # "General",
            ]
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
            # Gemini(data, Geminis.G3F),
        ]

        # Fire
        DRYRUN = True
        DRYRUN = False
        printer.thunder(f"Launching {data.topic}")
        launch_models(data, models, DRYRUN)


def create_prompt(topic: str):
    head = f"""# Summary Correction - {topic}\n"""
    return head + loop_prompt


loop_prompt = """
I created a summary for the exam,
it consist of 17 sections split in 12 `.tex` files.
The pdf of the summary is attached as reference,
2 pages and 11pt is mandatory, 4 columns is 95% fixed.

The task is to check the the attached `.tex` file,
compare it with the lecture material in the provided files,
give feedback and provide improvements.

- suggest corrections in case something is wrong or missing but important for the exam
- send snippets or the entire corrected file beside a brief explanation
"""

if __name__ == "__main__":
    thunder()
    # printer.print(create_prompt("tesT"))
