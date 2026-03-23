from typing import Annotated

import typer

Name = Annotated[
    str,
    typer.Option(
        "--name",
        "-n",
        help="Name of current target",
    ),
]
