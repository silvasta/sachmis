from pathlib import Path
from typing import Annotated

import typer

### --- --- --- --- --- --- --- --- --- --- ---
### --- General
### --- --- --- --- --- --- --- --- --- --- ---

Name = Annotated[
    str,
    typer.Option(
        "--name",
        "-n",
        help="Name of current target",
    ),
]

Async = Annotated[
    bool,
    typer.Option(
        "--async",
        "-a",
        help="Use async execution of online requests",
    ),
]

DryRun = Annotated[
    bool,
    typer.Option(
        "--dry",
        help="Simulate pipeline without execution",
    ),
]

### --- --- --- --- --- --- --- --- --- --- ---
### --- Sachmis Specific
### --- --- --- --- --- --- --- --- --- --- ---

Fire = Annotated[
    bool,
    typer.Option(
        "--direct-fire",
        "-D",
        help="Avoid confirmation step before API call",
    ),
]

### --- --- --- --- --- --- --- --- --- --- ---
### --- Specific for Fire (so far)
### --- --- --- --- --- --- --- --- --- --- ---

Models = Annotated[
    list[str] | None,
    # INFO: using Argument instead of Option allows easy list!
    typer.Argument(
        # "--model",
        # "-m",
        help="Encoded model name, no selection launches picker",
    ),
]


PickModel = Annotated[
    # REMOVE: not needede for fire, maybe somewhere else?
    bool,
    typer.Option(
        "--pick-model",
        "-M",
        help="Pick models from list!",
    ),
]

Files = Annotated[
    list[Path] | None,
    typer.Option(
        "--files",
        "-f",
        help="Add files from paths",
    ),
]
# LATER: check if Files/Models collapse
PickFiles = Annotated[
    bool,
    typer.Option(
        "--pick-files",
        "-F",
        help="Pick files from registry",
    ),
]
Images = Annotated[
    list[Path] | None,
    typer.Option(
        "--images",
        "-i",
        help="Add images from file paths",
    ),
]
PickImage = Annotated[
    bool,
    typer.Option(
        "--pick-images",
        "-I",
        help="Pick images from EXISTING FOLDER?",
    ),
]

PickRole = Annotated[
    bool,
    typer.Option(
        "--pick-role",
        "-R",
        help="Pick roles from existing list",
    ),
]
