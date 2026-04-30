import typer
from sstcore.cli.setup import attach_callback, logger_catch

from ...config import SachmisConfig, get_config
from ...config.model import Geminis, Groks, get_all_models
from ...utils.print import printer


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
    printer.lines_with_len(
        name="All Models",
        lines=[model.unique for model in get_all_models(with_dummy=True)],
    )
    printer.model_table(get_all_models())


@app.command("config")
@logger_catch
def config_details():
    """Print config to Console, so far just dotenv_path"""
    # MOVE: to silvasta? yes! some basic stats
    config: SachmisConfig = get_config()

    # REFACTOR: create subapp, config management etc
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
