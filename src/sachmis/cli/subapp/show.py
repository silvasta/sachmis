import typer
from silvasta.cli.setup import attach_callback, logger_catch

from sachmis.config.manager import config
from sachmis.config.model import Geminis, Groks
from sachmis.data import DataManager
from sachmis.utils.print import printer


def main() -> None:
    printer.title(f"Welcome to {__name__}!", style="sub-title")
    app()


app = typer.Typer(
    name="show",
    help="Show statistics, configurations and more",
    no_args_is_help=True,
)
attach_callback(app)


@app.command()
@logger_catch
def biome():
    """Show all Bases with Forest in Biome"""
    with DataManager(save_at_exit=False) as data:
        printer(data.biome)
        printer(f"{data.biome.n_forest=}")
        printer(f"{data.biome.n_responses=}")
        printer(f"{data.biome.roles=}")
        printer(f"{data.biome.n_roles=}")
        # LATER: create proper selection, maybe attach to printer


@app.command()
@logger_catch
def bases():
    """Show all Bases with Forest in Biome"""
    with DataManager(save_at_exit=False) as data:
        printer.path_exists_table(
            paths=data.biome.forests + data.biome.outdated_forests,
            header="Biome: Active and Outdated Forests",
        )


@app.command()
@logger_catch
def trees():
    """Show all Trees in Forest"""
    with DataManager(save_at_exit=False) as data:
        if not data.in_forest:
            printer.fail("No Forest no Trees")
        else:
            # LATER: adapt this to new setup
            printer.forest(data.forest)


@app.command()
@logger_catch
def files(
    cat: list[str] | None = None,
    # TODO: adapt to new setup
    topic: list[str] | None = None,
):
    """Show files and status inside file registry"""

    select: dict[str, list[str]] = {}
    # LATER: adapt this to new setup
    # MOVE: selection anyway needed in Forest
    if cat is not None:
        select["category"] = cat
    if topic is not None:
        select["topic"] = topic

    with DataManager(save_at_exit=False) as data:
        if not data.in_forest:
            printer.fail("No Forest no Files")
        else:
            raise NotImplementedError("create: printer.NEW(selection)")


@app.command()
@logger_catch
def models():
    """Show all models of all providers"""
    printer.title("Groks")
    for model in Groks:
        printer.md(
            f"-x {model.value:<6} {model:<14} **{model.api_name}**",
            style="blue",
        )
    # TODO: rich table, statistics
    # MOVE: to printer
    printer.title("Geminis")
    for model in Geminis:
        printer.md(
            f"-g {model.value:<6} {model:<14} **{model.api_name}**",
            style="green",
        )


@app.command("config")
@logger_catch
def config_details():
    """Print config to Console, so far just dotenv_path"""
    printer(config.defaults)
    printer(config.names)


@app.command()
@logger_catch
def roles():
    # TODO: create "new role" function (somewhere else)
    printer.fail("not avaliable")


if __name__ == "__main__":
    main()
