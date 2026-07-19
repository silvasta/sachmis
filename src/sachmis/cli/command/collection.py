from itertools import product

from sstcore import printer
from sstcore.cli import sargs
from typer import Context

from sachmis.config import SachmisConfig

from ...data.dag import PromptTransitionRules, ResponseTransitionRules
from ...data.operator._iret_camp_folder_setup import create_new_base
from .. import args
from ..scroll.model import conversation_transition_result, model_family_table


def init(ctx: Context, name: args.Name = ""):
    """Create new Camp with Forest and Local Data Structure"""
    config: SachmisConfig = ctx.obj["config"]
    name: str = name or config.names.camp_dir
    create_new_base(ctx.obj["system"], name)


def model_display():
    """Show all models of all providers"""
    model_family_table()


def rules():
    """Show Prompt / Response Relationship and Transitions"""

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

        conversation_transition_result(
            prompt, response, result=r_pr1, from_prompt=False
        )

        r_rp1: bool = prompt.valid_successor(response)
        r_rp2: bool = response.valid_ancestor(prompt)
        if r_rp1 != r_rp2:
            printer(f"{r_rp1=}-{r_rp2=}")
            printer.red("Inconsistent TransitionRules!")

        conversation_transition_result(
            prompt, response, result=r_rp1, from_prompt=True
        )


def config_details(ctx: Context, write_config: sargs.Write = False):
    """Print config() to Console, optional override json settings"""
    config: SachmisConfig = ctx.obj["config"]
    printer(config.settings)
    printer(config.paths.dot_env)
    printer(config.setting_file)

    if write_config:
        config.save_settings()
