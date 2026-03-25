import typer
from silvasta.cli.setup import attach_callback, logger_catch

from sachmis.utils.print import printer


def main() -> None:
    app()


app = typer.Typer(
    name="forest",
    help="Local folder structure managed by Forest",
    no_args_is_help=True,
)
attach_callback(app)


@app.command()
@logger_catch
def maybe_roll_out(ctx: typer.Context):
    """Expand condensed Forest data to file system"""
    printer.danger("Implement!")


if __name__ == "__main__":
    main()
