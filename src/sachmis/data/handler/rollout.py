from enum import StrEnum, auto
from pathlib import Path

from loguru import logger
from sstcore import PathGuard
from sstcore.data import SstFile

from ...config import SachmisConfig, get_config
from ...config.models import ModelSelectData
from ...config.models import uniques as model_uniques
from ...config.names import id_keywords_backwards
from ...exceptions import SachmisDataError, SachmisLaunchError
from ...utils import parse_raw_models, printer
from ..conversation import Prompt
from ..files import RolloutRegistry
from .handler import DataHandler

config: SachmisConfig = get_config()


class Status(StrEnum):
    UNDEFINED = auto()
    ROOT = auto()
    SINGLE = auto()
    LONG = auto()
    CROWD = auto()


class FileRollout(DataHandler):
    """Manage Prompt and Response write to Forest dir"""

    status: Status = Status.UNDEFINED

    filesystem_work_todo = True
    target_dir: Path = Path.cwd()

    result_files: list[Path] = []

    # NEXT:
    def _prepare_prompt_text(self):
        return self._prompt_text

    def __init__(self, prompt=True, forest=True):
        if prompt:
            self._load_prompt_text()

        if forest:
            self.scan_forest()

        self._print_entry()

    def scan_forest(self):
        """Build Registry with FileTree and RolloutTree of Forest"""

        self.registry: RolloutRegistry = RolloutRegistry.ready()

        if (tree_schema := self.registry.find_tree_above()) is None:
            if not config.paths.cwd_in_top_dir:
                raise SachmisLaunchError("Bad Location, Sprout has not Tree!")
            self.scanned_tree_id = 0
        else:
            self.scanned_tree_id: int = tree_schema.tree_id

    def get_sprout_groups(self) -> dict[str, list[SstFile]]:
        sprout_groups: dict[str, list[SstFile]] = (
            self.registry.get_folder_member_grouped_by_id_keyword()
        )
        logger.info(f"Found {len(sprout_groups.keys())} Sprouts in CWD")
        return sprout_groups

    def models(self) -> list[ModelSelectData]:
        return self._filter_model_select_data_from_sprout_group()

    def _filter_model_select_data_from_sprout_group(self):
        all_models: set[str] = model_uniques()

        model_select_data: list[ModelSelectData] = []

        for sprout_id, sprout_files in self.get_sprout_groups().items():
            self._print_stuff(sprout_id, sprout_files)

            for file in sprout_files:
                printer.title(f"Start of: {file}")

                # Filter if keyword is in models
                if model_unique := file.keywords & all_models:
                    printer.success(f"Found Model: {model_unique=}")
                    if len(model_unique) != 1:
                        raise SachmisDataError("Error in Registry Keywords")
                    data: ModelSelectData = self._create_model_select_data(
                        file, model_unique.pop()
                    )
                    model_select_data.append(data)
        return model_select_data

    def _create_model_select_data(
        self, file: SstFile, model_unique: str
    ) -> ModelSelectData:

        if not (model := parse_raw_models([model_unique])):
            raise SachmisDataError(f"Bad Parameter in {file}")

        # NEXT:
        # NEXT:
        # NEXT:
        # NEXT:
        # NEXT:
        return ModelSelectData.from_data(
            model=model[0],
            tree_id=id_keywords_backwards("tree", file.keywords),
            sprout_id=id_keywords_backwards("sprout", file.keywords),
        )

    def _print_stuff(self, sprout_id, sprout_files):  # REMOVE
        printer.special(f"Start of Detected Sprout: {sprout_id}")
        printer([file for file in sprout_files])
        printer.banner("Go")

    def _handle_response_by_responsibility(
        self, model, topic, sprout_id, tree_id=0
    ):

        # NEXT:
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

    @property  # REFACTOR:
    def output_prompt_path(self):
        return self.target_dir / f"{self.prompt_stem}.md"

    @property  # REFACTOR:
    def current_response_path(self):
        return self.target_dir / f"{self.response_stem}.md"

    # REFACTOR:
    def prepare_sprout_stems(self, model, topic, sprout_id):
        self.prompt_stem: str = config.names.prompt_stem(sprout_id, topic)
        self.response_stem: str = config.names.response_stem(
            sprout_id, model.unique, topic
        )  # WARN: here will come only 1 prompt but n responses
        printer.lines([self.prompt_stem, self.response_stem])

    def rotate_prompt(self):
        PathGuard.rotate(
            source=self.input_prompt_path,
            target=self.output_prompt_path,
            reset=True,
        )
        # Generate new empty prompt in target dir
        self.output_prompt_path.with_name(self.input_prompt_path.name).touch()
        logger.debug(f"prompt rotated: {self.output_prompt_path}")

    def dispatch_action(self):
        # TASK: arguments, Prompt/Response probably not, also not Tree
        match self.status:
            case Status.UNDEFINED:  # LATER: remove
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
