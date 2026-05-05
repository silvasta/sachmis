from sstcore.cli import logger_catch

from ...config import SachmisConfig, get_config
from ...config.model import Geminis, Groks, get_all_models
from ...data.setup import create_new_base
from ...utils.print import printer
from .. import args

config: SachmisConfig = get_config()


@logger_catch
def init(name: args.Name = config.names.base_dir):
    """Create new Base with Forest and Local Data Structure"""
    create_new_base(name)


@logger_catch
def models():  # TODO: rich table, statistics
    """Show all models of all providers"""

    printer.title("Groks")
    for model in Groks:
        printer.md(
            f"-x {model.value:<6} {model:<14} **{model.api_name}**",
            style="normal",
        )

    printer.title("Geminis")
    for model in Geminis:
        printer.md(
            f"-g {model.value:<6} {model:<14} **{model.api_name}**",
            style="normal",
        )
    printer.lines_with_len(
        name="All Models",
        lines=[model.unique for model in get_all_models(with_dummy=True)],
    )
    printer.model_table(get_all_models())


@logger_catch
def roles():  # TODO: create "new role" function (somewhere else)
    # TASK: where to place? solve together with local|global role
    printer.danger("not available")


@logger_catch
def config_details(save: bool = False):
    """Print config to Console, so far just dotenv_path"""
    # MOVE: to silvasta? yes! some basic stats
    config: SachmisConfig = get_config()

    # TODO: save settings? load updates from json? or push updates down to json?
    # REFACTOR: create subapp, config management etc
    printer(config.compose_setup_param())  # LATER: show selection of paths
    printer(config.settings)
    printer(config.paths.dot_env)  # LATER: show selection of paths
    printer(config.master_setting_file)  # LATER: show selection of paths
    if save:
        config.save_settings()
