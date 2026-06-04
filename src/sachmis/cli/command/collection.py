from itertools import product

from sstcore.cli import logger_catch, sargs

from sachmis.data.conversation import (
    PromptTransitionRules,
    ResponseTransitionRules,
)

from ...config import SachmisConfig, get_config, models
from ...data.setup import create_new_base
from ...utils.print import printer
from .. import args

config: SachmisConfig = get_config()


def init(name: args.Name = config.names.base_dir):
    """Create new Base with Forest and Local Data Structure"""
    create_new_base(name)


def model_display():  # TODO: rich table, statistics
    """Show all models of all providers"""
    printer.model_table(models.uniques(), models.names(), models.api_names())


@logger_catch
def rules():
    def _explain(rule: type):
        printer.title(name := rule.__name__)
        printer.header(
            rule.__doc__, title=name, text_style="white", title_align="right"
        )

    _explain(PromptTransitionRules)
    _explain(ResponseTransitionRules)

    for prompt, response in list(
        product(PromptTransitionRules, ResponseTransitionRules)
    ):
        r_pr1: bool = prompt.valid_ancestor(response)
        r_pr2: bool = response.valid_successor(prompt)
        if r_pr1 != r_pr2:
            printer(f"{r_pr1=}-{r_pr2=}")
            printer.red("Inconsistent TransitionRules!")

        printer.conversation_transition_result(
            prompt,
            response,
            result=r_pr1,
            from_prompt=False,
        )

        r_rp1: bool = prompt.valid_successor(response)
        r_rp2: bool = response.valid_ancestor(prompt)
        if r_rp1 != r_rp2:
            printer(f"{r_rp1=}-{r_rp2=}")
            printer.red("Inconsistent TransitionRules!")

        printer.conversation_transition_result(
            prompt,
            response,
            result=r_rp1,
            from_prompt=True,
        )


def config_details(write_config: sargs.Write = False):
    """Print config to Console, optional override the json settings"""
    config: SachmisConfig = get_config()  # TODO: better selection
    printer(config.setup_info)
    printer(config.settings)
    printer(config.paths.dot_env)
    printer(config.setting_file)

    if write_config:
        config.save_settings()
