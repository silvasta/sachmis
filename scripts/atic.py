from pathlib import Path

from loguru import logger
from silvasta.utils.log import setup_logging

import sachmis.core.capstone as cap
from sachmis.config.model import Groks
from sachmis.data import DataManager
from sachmis.utils.print import printer


def thunder():
    # Log setup
    log_level = "DEBUG"
    setup_logging(log_level_override=log_level)

    # Data setup
    logger.info("Starting Data")
    with DataManager() as data:
        printer.title("Prompt", style="bold white on blue")
        data.load_prompt()
        printer.md(data._prompt)

        data.load_role(
            Path(
                "/home/silvan/Code/sachmis/main/data/homes/share/roles/structured-senior-engineer.txt"
            )
        )
        data.load_images([])

        for file in data.forest.files:
            if not file.name.startswith("Pag"):
                continue

            data._files = [file]

            printer.title("Models", style="bold white on blue")

            models = cap.load_models(data, [Groks.G420M])

            # Fire
            DRYRUN = True
            DRYRUN = False

            printer.warn(f"Launching {models}")
            cap.launch_models(models, dry_run=DRYRUN)

    printer.success("Models finished to run, storing data, au revoir!")


if __name__ == "__main__":
    thunder()
