import typer
from silvasta.cli.setup import attach_callback

from sachmis.cli import command, subapp


def main() -> None:
    app()


# main
app = typer.Typer(
    name="sachmis",
    help="CLI for direct communication with LLMs",
    no_args_is_help=True,
)
attach_callback(app)

# core
app.command()(command.fire)
app.command()(command.tree)  # NEXT:
# app.command()(command.loop)
# app.command()(command.thunder)

# utils
app.command("monitor")(command.launch_monitor)
app.command()(command.data)
app.command("print")(command.print_file)

# nested
app.add_typer(subapp.init)
app.add_typer(subapp.files)  # NEXT:
# app.add_typer(subapp.forest)
app.add_typer(subapp.show)


if __name__ == "__main__":
    main()
