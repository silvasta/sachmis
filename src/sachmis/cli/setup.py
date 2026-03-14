# INFO: Try first with silvasta.cli.setup, otherwise modify below

# def main_callback(verbose: bool, quiet: bool):
#     """Setup logging (data, etc...) for app executed as main app"""
#     printer.title(f"Start of: {__name__}!", style="title")
#     # Setup logging
#     level: str | None = "DEBUG" if verbose else None
#     setup_logging(log_level_override=level, quiet=quiet)
#
#
# def sub_callback():
#     """Provide information for subapps that help users to navigate"""
#     printer.title(f"Welcome to sub module {__name__}!", style="title")

# INFO: Try first with silvasta.cli.setup, otherwise modify below

# def attach_callback(app: typer.Typer):
#     """Register  single dispatcher callback to the app"""
#
#     @app.callback()
#     def dispatcher(
#         ctx: typer.Context,
#         verbose: bool = typer.Option(False, "--verbose", "-v", help="Show debug logs"),
#         quiet: bool = typer.Option(False, "--quiet", "-q", help="Terminal output"),
#     ):
#         if ctx.parent is None:
#             main_callback(verbose, quiet)
#         else:
#             sub_callback()
