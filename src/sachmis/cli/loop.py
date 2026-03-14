import typer

from ..utils.log import logger_catch
from ..utils.print import printer


# def main() -> None:
#     printer.title(f"Welcome to {__name__}!", style="sub-title")
#     app()
#
#
# app = typer.Typer(
#     name="loop",
#     help="Iterate according to schema",
#     no_args_is_help=True,
# )
#
#
# @app.callback()
# def main_callback(ctx: typer.Context):
#     printer.title(f"Welcome to {__name__}!", style="sub-title")
#
#
# @app.command()


@logger_catch
def loop():
    """launch pipeline (Coming Soon)"""
    # TASK: pipeline for multiple prompts
    # - reuse previous responses
    # - ultimate reasoning
    printer.md("the loop is startig!")


# if __name__ == "__main__":
#     main()
