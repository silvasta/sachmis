from itertools import product

from sstcore.cli import logger_catch, sargs

from sachmis.data.conversation import (
    PromptTransitionRules,
    ResponseTransitionRules,
)

from ...config import (
    Geminis,
    Groks,
    SachmisConfig,
    get_config,
    model_api_names,
    model_uniques,
)
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
        lines=[model for model in model_uniques()],
    )
    printer.model_table(model_uniques(), model_api_names())


@logger_catch
def rules():
    PromptTransitionRules.explain()

    for prompt, response in list(
        product(PromptTransitionRules, ResponseTransitionRules)
    ):
        print(prompt)
        print(response)
        printer.show_conversation_transition_result(
            printer._format(prompt), response
        )

    # printer.red(
    #     i
    #     for i in [
    #         y.description(),
    #         y.explain(),
    #         a.explain(),
    #         z.description(),
    #     ]
    # )


@logger_catch
def roles():  # TODO: create "new role" function (somewhere else)
    # TASK: where to place? solve together with local|global role
    printer.danger("not available")


@logger_catch
def config_details(write_config: sargs.Write = False):
    """Print config to Console, optional override the json settings"""
    config: SachmisConfig = get_config()  # TODO: better selection
    printer(config.setup_info)
    printer(config.settings)
    printer(config.paths.dot_env)
    printer(config.setting_file)

    if write_config:
        config.save_settings()
