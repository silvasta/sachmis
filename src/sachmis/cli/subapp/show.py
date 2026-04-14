import typer
from silvasta.cli.setup import attach_callback, logger_catch

from sachmis.config import SachmisConfig, get_config
from sachmis.config.model import Geminis, Groks
from sachmis.data import DataManager
from sachmis.utils.print import printer


def main() -> None:
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
    """Show Biome information"""
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
    """Show all Bases with Forest that are saved in Biome"""
    with DataManager(save_at_exit=False) as data:
        printer.path_exists_table(
            paths=data.biome.forests + data.biome.outdated_forests,
            header="Biome: Active and Outdated Forests",
        )


@app.command()
@logger_catch
def trees():
    """Show all Trees in Forest"""
    with DataManager(save_at_exit=False, forest_required=True) as data:
        # printer.forest(data.forest) # TASK: repair: printer.tree
        printer(data.forest)


@app.command()
@logger_catch
def files(  # NEXT: adapt this to new setup
    cat: list[str] | None = None,
    # TODO: adapt to new setup
    topic: list[str] | None = None,
):
    """Show files and status inside file registry"""

    # MERGE: Files?
    select: dict[str, list[str]] = {}
    if cat is not None:
        select["category"] = cat
    if topic is not None:
        select["topic"] = topic

    with DataManager(save_at_exit=False, forest_required=True) as data:
        raise NotImplementedError("create: printer.NEW(selection)")


@app.command()
@logger_catch
def models():  # TODO: rich table, statistics
    """Show all models of all providers"""

    printer.title("Groks")
    for model in Groks:  # MOVE: to printer, attach to ModelFamily?
        printer.md(
            f"-x {model.value:<6} {model:<14} **{model.api_name}**",
            style="normal",
        )

    # HACK: General Collector for all (active) models?
    # (check picker,show-app,others)

    printer.title("Geminis")
    for model in Geminis:  # MOVE: to printer, attach to ModelFamily?
        printer.md(
            f"-g {model.value:<6} {model:<14} **{model.api_name}**",
            style="normal",
        )


@app.command("config")
@logger_catch
def config_details():
    """Print config to Console, so far just dotenv_path"""
    config: SachmisConfig = get_config()

    printer(config.compose_setup_param())  # LATER: show selection of paths
    printer(config.settings)
    printer(config.paths.dot_env)  # LATER: show selection of paths
    printer(config.master_setting_file)  # LATER: show selection of paths


@app.command()
@logger_catch
def roles():  # TODO: create "new role" function (somewhere else)
    printer.danger("not avaliable")


if __name__ == "__main__":
    main()
