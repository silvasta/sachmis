import re
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
    role = """You are an expert in Game Theory,
you know which topics are relevant for summaries and exams
and you have the ability to pack a lot of information into a compact text"""
    data.system_role: str = role
    logger.info(f"{role=}")

    topics: list[str] = [
        "empty"
        # "static-games",
        # "zero-sum-games",
        # "auctions",
        # "potential-games",
        # "convex-games",
        # "stackelberg-games",
        # "repeated-games",
        # "multistage-games",
        # "dynamic-games",
        # "stochastic-games",
        # "2024",
        # "2025",
    ]
    categories: list[str] = [
        # "Lecture",
        # "Tutorial",
        "Exam",
        # "Exercise",
        "Tex",
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
        data.files: list[File] = []

        # data.files += data.forest.file_selection(
        #     topics=[topic],
        #     categories=categories,
        # )
        data.files += data.forest.file_selection(
            # topics=topics,
            categories=categories,
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
            # Grok(data, Groks.G41FR),
            # Grok(data, Groks.G4),
            Gemini(data, Geminis.G3F),
        ]

        # Fire
        DRYRUN = True
        DRYRUN = False
        printer.thunder(f"Launching {data.topic}")
        launch_models(data, models, DRYRUN)


def create_prompt(topic: str):
    return f""" # Example Exercises for Topic {topic}

In the attached files you find the material for the {topic=} to cover in this step.

I wrote a summary for the lecture 'Game Theory and Control' from ETH Zurich.
It has 10 chapters, each of them is in one file.
The summary is fine so far, it is mainly as information which topics are relevant and covered in the lecture, I can't use a summary during the exam.
There is also an exercise appended from the current topic, use it as reference and take ideas from there.

The exam is tomorrow, below is an overview about last years tasks.
For now I need example exercises and instructions how to solve them on paper.
The instructions should be such that I can solve it now on paper and with a second check of the instructions just before the exam it should be fine.

## Task

- Check the summaries, especially the current topic
- Create example exam questions for the current topic
- Provide methods how to solve them

Markdown format is probably fine, but no requirement.

## Summary of Past Exams

### Past Exam: February 2024 (Game Theory and Control Final Exam)

**Brief Topic Summary**:  
The exam covers foundational non-cooperative game theory concepts (solution refinement, potential games, evolutionary dynamics), applied pricing competition (ride-hailing platforms with Stackelberg leadership), and extensive-form zero-sum games (behavioral vs. mixed strategies).

**Relevant Keywords**: security level, pure/mixed/admissible Nash equilibrium, potential game, ESS, replicator dynamics, Bertrand competition, price cap, substitutability, convex game, strong monotonicity, Stackelberg equilibrium, extensive-form game, information sets, feedback game, behavioral/mixed strategy, Kuhn’s theorem.

### Past Exam: February 2025 (Game Theory and Control Final Exam)

**Brief Topic Summary**:  
The exam emphasizes repeated games (altruistic/selfish behavior with trigger strategies), continuous-action power control (wireless SINR games with convergence dynamics), and stochastic dynamic games (epidemic modeling with finite-horizon backward induction).

**Relevant Keywords**: altruism/selfishness, potential function, best-response dynamics, repeated games, trigger strategy, SINR, power control, convex game, strict monotonicity, projected gradient iteration, contractive mapping, stochastic game, epidemic behavior, backward induction, finite-horizon dynamic game, pure-strategy Nash equilibrium.
"""


def get_num(file_name: str) -> int | None:
    """As defined above."""
    match = re.match(r"^([ELT])(\d+)", file_name)
    if match:
        return int(match.group(2))
    else:
        logger.warning(f"Unable to extract number from file name: {file_name}")


if __name__ == "__main__":
    thunder()
