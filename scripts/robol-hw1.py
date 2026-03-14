from string import Template
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


# FOLDER = "networks"
FOLDER = "transformers"


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
    role = """You are an expert in Machine Learning with focus on applications in Robotics,
you know how to create and explain a reusable Pytorch setup"""
    data.system_role: str = role
    logger.info(f"{role=}")

    topics: list[str] = [
        # "basic-layers",
        # "normalization",
        # "mlp-and-residual-networks",
        # "classification-problem",
        "transformers"
    ]
    create_files = True
    create_files = False
    if create_files:
        base_path = Path.home() / f"Coding/python/libraries/torch/{FOLDER}"
        # TODO: create similar function in DataManager like used in setup below
        descriptions: list[Path] = [base_path / f"{topic}.md" for topic in topics]
        codes: list[Path] = [base_path / f"{topic}.py" for topic in topics]
        # TODO: extract automatic file setup
        for description, code in zip(descriptions, codes):
            description.touch()
            code.touch()
            printer.print(description)
            printer.print(code)
        return

    categories: list[str] = []

    for topic in topics:
        # Prompt
        printer.title("Prompt", style="bold white on blue")
        load_from_file = True
        load_from_file = False
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
        # data.files += data.forest.file_selection(
        #     # topics=topics,
        #     categories=categories,
        # )
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
        DRYRUN = False
        printer.thunder(f"Launching {data.topic}")
        launch_models(data, models, DRYRUN)


def create_prompt(topic: str) -> str:
    # TODO: generalize this in main tool
    # NOTE: use robust loading from DataManager
    # prompt_path: Path = Path.cwd() / "loop-prompt.md"
    prompt_path: Path = Path.cwd() / "loop-prompt-task4.md"
    prompt_template = Template(prompt_path.read_text())

    base_path: Path = Path.home() / f"Coding/python/libraries/torch/{FOLDER}"
    description: str = (base_path / f"{topic}.md").read_text()
    code: str = (base_path / f"{topic}.py").read_text()

    replacements: dict[str, str] = {
        "TOPIC": topic,
        "DESCRIPTION": description,
        "CODE": code,
    }
    # return prompt_template.substitute(replacements)
    # NOTE: use this for math mode, fails silent when $KEY_NOT_HERE
    return prompt_template.safe_substitute(replacements)


if __name__ == "__main__":
    thunder()
