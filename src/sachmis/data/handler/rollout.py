from enum import StrEnum, auto
from pathlib import Path

from loguru import logger
from sstcore import PathGuard
from sstcore.utils import PathFilter, PathTreeNode, ProjectFilter
from sstcore.utils.filter import StemFilter
from sstcore.utils.parse import ParsedName
from sstcore.utils.print import ColorBox
from sstcore.utils.scanner import FolderScanner

from sachmis.config.names import (
    PromptNameSchema,
    ResponseNameSchema,
    TreeNameSchema,
)

from ...config import SachmisConfig, get_config
from ...config.models import ModelFamily, all
from ...exceptions import DataRuntimeError
from ...utils.print import printer

config: SachmisConfig = get_config()

c: ColorBox = ColorBox()
c._colors.black = "dark_goldenrod"

text = f"{c.black('TreeIDMissingError')} Important for the Order!"


# NEXT: map this
def scan_and_parse_forest_dir():
    project: FolderScanner = ToolBox.PROJECT.scanner(config.paths.base_dir)
    tree: FolderScanner = ToolBox.TREE.scanner(config.paths.base_dir)
    prompt: FolderScanner = ToolBox.PROMPT.scanner(config.paths.base_dir)
    response: FolderScanner = ToolBox.RESPONSE.scanner(config.paths.base_dir)

    all: list[FolderScanner] = [project, tree, prompt, response]
    printer(all)


class Status(StrEnum):
    OUTSIDE_FOREST = auto()
    ROOT = auto()
    SINGLE = auto()
    LONG = auto()
    CROWD = auto()

    # @property
    # def action(self) -> bool:
    #     return self in {self.DEFAULT, self.ROOT}

    def models(self, pick_model) -> list[ModelFamily]:
        printer(f"{pick_model=}")
        match self:
            case self.ROOT:
                return all()
            case self.OUTSIDE_FOREST:
                return []


class FileRollout:
    """Manage Prompt and Response write to Forest dir"""

    topic: str = ""
    tree_id = 0
    sprout_id = 0
    status: Status = Status.OUTSIDE_FOREST

    has_selected = False
    filesystem_work_todo = True
    target_dir: Path = Path.cwd()

    tree_model: TreeNameSchema
    promp_model: PromptNameSchema
    response_model: ResponseNameSchema

    result_files: list[Path] = []

    def models():  # NEXT:
        raise NotImplementedError

    def prompt_text():  # NEXT:
        raise NotImplementedError

    def process():  # NEXT:
        raise NotImplementedError

    @property
    # REFACTOR:
    def output_prompt_path(self):
        return self.target_dir / f"{self.prompt_stem}.md"

    @property
    # REFACTOR:
    def current_response_path(self):
        return self.target_dir / f"{self.response_stem}.md"

    def __init__(self):
        # NEXT: hold all here? maybe new Registry! with new Tree
        self.tree_parser: ParsedName = config.names.tree_parser
        self.prompt_parser: ParsedName = config.names.prompt_parser
        self.answer_parser: ParsedName = config.names.response_parser

        self.input_prompt_path: Path = config.paths.input_prompt

        # NEXT: what needed?
        self._print_entry()  # REMOVE:

    def scan_forest(self):  # WARN: must be triggered?
        """Delayed after init scan the entire Forest and map Structure"""

        if config.paths.cwd_in_top_dir:
            self.status: Status = Status.ROOT
            printer.title(f"{self.status=}: waiting for Tree ID")
        else:  # NEXT: map this
            self.extract_tree_id()

    def extract_tree_id(self):  # TODO: check with new folder scanner
        tree_stem: str = config.paths.cwd_to_base_dir().parts[0]
        self.tree_model: TreeNameSchema = self.tree_parser(tree_stem)
        self.tree_id: int = self.tree_model.tree_id

    def attach_tree_id(self, id: int):
        """Triggered from Sprout after Tree is loaded"""
        # IDEA: maybe provide here the prompt text

        if self.status.ROOT and not id or not self.tree_id:
            printer.header(text, frame="orange_red1")
            raise DataRuntimeError(
                "Invalid control flow, FileRollout has no Tree ID"
            )
        self.tree_id: int = id

    def load_prompt_text(self):  # NEXT: as function of Prompt!
        logger.info(f"Loading prompt text from: {self.input_prompt_path=}")
        self.prompt_text: str = self.input_prompt_path.read_text()
        return self.prompt_text

    def action_init(self):
        """Setup new tree dir"""
        printer.header(f"Start of Init: {self.status}", frame="purple")

        tree_stem: str = config.names.tree_stem(self.tree_id, self.topic)
        printer(tree_stem)
        self.filesystem_work_todo = False
        # IDEA: delayed and applied by decorator at path generation?
        self.target_dir: Path = PathGuard.dir(tree_stem)

    def action_chain(self):
        """Make a single prompt (line) longer"""
        printer.header(f"Start of Chain: {self.status}", frame="purple")

    def action_dig(self):
        """Make new subfolder and copy existing prompt/response"""
        printer.header(f"Start of Dig: {self.status}", frame="purple")

    def dispatch_action(self):
        # TASK: arguments, Prompt/Response probably not, also not Tree
        match self.status:
            case Status.OUTSIDE_FOREST:  # LATER: remove
                printer.danger("Response Outside Forest!!!")
            case Status.ROOT:
                self.action_init()
            case Status.SINGLE:
                self.action_chain()
            case Status.LONG:
                if self.has_selected:
                    self.action_dig()
                else:
                    self.action_chain()
            case Status.CROWD:
                self.action_dig()

    # NEXT:
    def process(self, model, topic, sprout_id, tree_id=0):
        """Dispatch Execution on Filesystem depending on Status"""

        self.tree_id: int = tree_id or self.tree_id
        self.prepare_sprout_stems(model, topic, sprout_id)

        if self.filesystem_work_todo:
            self.dispatch_action()
            self.rotate_prompt()
            self.filesystem_work_todo = False

        self.write_response()  # NEXT: args

    # IMPORTANT: from here:
    # REFACTOR: all to _self methods
    #
    def write_response(self):  # NEXT: args
        pass

    def rotate_prompt(self):
        PathGuard.rotate(
            source=self.input_prompt_path,
            target=self.output_prompt_path,
            reset=True,
        )
        # Generate new empty prompt in target dir
        self.output_prompt_path.with_name(self.input_prompt_path.name).touch()
        logger.debug(f"prompt rotated: {self.output_prompt_path}")

    def prepare_sprout_stems(self, model, topic, sprout_id):
        self.prompt_stem: str = config.names.prompt_stem(sprout_id, topic)
        self.response_stem: str = config.names.response_stem(
            sprout_id, model.unique, topic
        )  # WARN: here will come only 1 prompt but n responses
        printer.lines([self.prompt_stem, self.response_stem])

    def _print_entry(self):
        if not config.paths.in_forest:
            printer.danger("Outside Forest Dir!")
        else:
            to_base: Path = config.paths.cwd_to_base_dir()
            printer.title(["Location: ", to_base], frame="purple")
            printer(Path.cwd())  # REMOVE:


class ToolBox(StrEnum):
    PROJECT = auto()
    TREE = auto()
    PROMPT = auto()
    RESPONSE = auto()

    def filter(self) -> PathFilter:
        match self:
            case self.PROJECT:
                return ProjectFilter()
            case self.TREE:
                return StemFilter(parser=config.names.tree_parser)
            case self.PROMPT:
                return StemFilter(parser=config.names.prompt_parser)
            case self.RESPONSE:
                return StemFilter(parser=config.names.response_parser)

    def scanner(self, root) -> FolderScanner:
        return FolderScanner(scan_root=root, path_filter=self.filter())

    def tree(self, root) -> PathTreeNode:
        return self.scanner(root).tree()

    def plot(self, root):
        printer.header(f"Parsing: {self}", frame="purple")
        printer.tree_graph(self.scanner(root).tree())
