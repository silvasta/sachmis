from enum import StrEnum, auto
from pathlib import Path

from loguru import logger
from sstcore import PathGuard
from sstcore.utils.print import ColorBox

from ...config import SachmisConfig, get_config
from ...utils.print import printer
from ..conversation import Prompt
from ..local_dir import RolloutRegistry
from .handler import DataHandler

config: SachmisConfig = get_config()

c: ColorBox = ColorBox()
c._colors.black = "dark_goldenrod"

text = f"{c.black('TreeIDMissingError')} Important for the Order!"


class Status(StrEnum):
    OUTSIDE_FOREST = auto()
    ROOT = auto()
    SINGLE = auto()
    LONG = auto()
    CROWD = auto()


class FileRollout(DataHandler):
    """Manage Prompt and Response write to Forest dir"""

    status: Status = Status.OUTSIDE_FOREST

    filesystem_work_todo = True
    target_dir: Path = Path.cwd()

    result_files: list[Path] = []

    def models(self):  # NEXT:
        raise NotImplementedError

    def _prepare_prompt_text(self):
        return self._prompt_text

    @property
    # REFACTOR:
    def output_prompt_path(self):
        return self.target_dir / f"{self.prompt_stem}.md"

    @property
    # REFACTOR:
    def current_response_path(self):
        return self.target_dir / f"{self.response_stem}.md"

    def __init__(self, prompt=True, forest=True):
        if prompt:
            self._load_prompt_text()

        if forest:
            self.scan_forest()

        self._print_entry()

    def scan_forest(self):
        """Build Registry with FileTree and RolloutTree of Forest"""

        self.registry: RolloutRegistry = RolloutRegistry.ready()
        self.registry.get_neighbours()

        if Path.cwd().parent != config.paths.base_dir:
            # IDEA: use registry level of folder?
            self.scanned_tree_id = self.registry.get_tree_id_above(Path.cwd())

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

    # REMOVE:
    def prepare_sprout_stems(self, model, topic, sprout_id):
        self.prompt_stem: str = config.names.prompt_stem(sprout_id, topic)
        self.response_stem: str = config.names.response_stem(
            sprout_id, model.unique, topic
        )  # WARN: here will come only 1 prompt but n responses
        printer.lines([self.prompt_stem, self.response_stem])

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

    def _print_entry(self):  # TODO: clean entry prints
        if not config.paths.in_forest:
            printer.danger("Outside Forest Dir!")
        else:
            to_base: Path = config.paths.cwd_to_base_dir()
            printer.title(["Location: ", to_base], frame="purple")
            printer(Path.cwd())

    def _load_prompt_text(self):
        self.input_prompt_path: Path = config.paths.input_prompt
        logger.info(f"Loading prompt text from: {self.input_prompt_path=}")
        self._prompt_text: str = self.input_prompt_path.read_text()
        self.topic: str = Prompt.extract_topic(self._prompt_text)
