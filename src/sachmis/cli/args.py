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
        "-n",  # FIX: dont workt in: sachmis biome setup
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

OutputFile = Annotated[
    # WARN: check collision with Files
    Path | None,
    typer.Option(
        "--output-file",
        "-o",
        help="Choose custom output file path",
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

Xai = Annotated[
    bool,
    typer.Option(
        "--xai",
        "-x",
        help="Upload files to xAI file registry",  # TODO: change to more general name
    ),
]
Google = Annotated[
    bool,
    typer.Option(
        "--google",
        "-g",
        help="Upload files to Google file registry",  # TODO: change to more general name
    ),
]
### --- --- --- --- --- --- --- --- --- --- ---
### --- Specific for Fire, Tree
### --- --- --- --- --- --- --- --- --- --- ---

Models = Annotated[
    list[str] | None,  # REMOVE: None?
    # INFO: using Argument instead of Option allows easy list!
    typer.Argument(
        # "--model",
        # "-m",
        help="Encoded model name, no selection launches picker",
    ),
]

Sprout = Annotated[
    bool,
    typer.Option(
        "--sprout",
        "-s",
        help="Select existing Sprout to create new branch from there",
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

PickFile = Annotated[
    bool,
    typer.Option(
        "--pick-file",
        "-F",
        help="Pick files from registry",  # TASK: implement picker for UploadFiles
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
        "--pick-image",
        "-I",
        help="Pick images from EXISTING FOLDER?",
    ),
]

PickRole = Annotated[
    bool,
    typer.Option(
        "--pick-role",
        "-R",  # IMPORTANT: how to use this for disabling pick-role?
        help="Pick roles from existing list",
    ),
]
