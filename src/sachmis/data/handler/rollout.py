from enum import StrEnum, auto
from pathlib import Path

from loguru import logger
from sstcore import PathGuard
from sstcore.data import SstFile

from ...config import SachmisConfig, get_config
from ...config.models import uniques as model_uniques
from ...config.names import id_keywords_backwards
from ...exceptions import SachmisDataError, SachmisLaunchError
from ...utils import model_from_unique, printer
from ..conversation import Prompt, Response, SproutSelectData
from ..files import RolloutRegistry
from .handler import DataHandler


class Status(StrEnum):
    UNDEFINED = auto()
    ROOT = auto()
    SINGLE = auto()
    LONG = auto()
    CROWD = auto()


class FileRollout(DataHandler):
    """Manage Prompt and Response write to Forest dir"""

    status: Status = Status.UNDEFINED
    result_files: list[Path] = []
    write_dir: Path = Path.cwd()

    def __init__(self, prompt=True, forest=True):
        if prompt:
            self._load_prompt_text()
        if forest:
            self.scan_forest()
        self._print_entry()

    def _handle_response_end_processing(self, response: Response):
        config: SachmisConfig = get_config()
        logger.info(f"Handling {response=}")

        if self.status == Status.UNDEFINED:
            self._check_cwd_and_tasks()

        response_file: Path = config.paths.response_file(
            self.write_dir, response.sprout_id, response.model, response.topic
        )
        logger.info(response_file)

        response_file.write_text(response.content)

    def _check_cwd_and_tasks(self):
        config: SachmisConfig = get_config()

        if config.paths.cwd_in_top_dir:
            self.status: Status = Status.ROOT
            self.action_init()
            self.rotate_prompt()
            return

        models: set[str] = self.registry.get_model_at_path()

        if len(models) == 1:
            # WARN: ignores multitple of same model
            self.status: Status = Status.SINGLE
            self.action_chain()
        else:  # TASK: dispatch for long
            #  case Status.LONG:
            #     if self.has_selected:
            #         self.action_dig()
            #       else: stay()?
            self.status: Status = Status.CROWD
            self.action_dig()
            self.rotate_prompt()

    def rotate_prompt(self):
        config: SachmisConfig = get_config()
        prompt_path: Path = config.paths.prompt_file(
            self.write_dir, self.prompt.sprout_id, self.prompt.topic
        )
        PathGuard.rotate(
            source=self.input_prompt_path, target=prompt_path, reset=True
        )
        # Generate new empty prompt in target dir
        prompt_path.with_name(self.input_prompt_path.name).touch()
        logger.debug(f"prompt rotated: {prompt_path}")

    def action_init(self):
        """Setup new tree dir"""
        config: SachmisConfig = get_config()
        printer.header(f"Start of Init: {self.status}", frame="purple")

        tree_stem: str = config.names.tree_stem(self.tree_id, self.topic)
        printer(tree_stem)
        self.filesystem_work_todo = False
        # IDEA: delayed and applied by decorator at path generation?
        self.write_dir: Path = PathGuard.dir(tree_stem)
        logger.info(f"Target Dir created: {tree_stem}")

    def action_chain(self):
        """Make a single prompt (line) longer"""
        # Nothing required
        printer.header(f"Start of Chain: {self.status}", frame="purple")

    def action_dig(self):
        """Make new subfolder and copy existing prompt/response"""
        config: SachmisConfig = get_config()
        printer.header(f"Start of Dig: {self.status}", frame="purple")

        previous_stem = config.names.response_stem(
            self.tree_id, self.selection_previous.model.unique, self.topic
        )
        self.write_dir: Path = PathGuard.dir(previous_stem)
        logger.info(f"Target Dir created: {previous_stem}")

    def _print_entry(self):  # TODO: clean entry prints
        config: SachmisConfig = get_config()
        if not config.paths.in_forest:
            printer.danger("Outside Forest Dir!")
        else:
            to_base: Path = config.paths.cwd_to_base_dir()
            printer.title(["Location: ", to_base], frame="purple")
            printer(Path.cwd())

    def _load_prompt_text(self):
        config: SachmisConfig = get_config()

        self.input_prompt_path: Path = config.paths.input_prompt
        logger.info(f"Loading prompt text from: {self.input_prompt_path=}")
        self._prompt_text: str = self.input_prompt_path.read_text()
        self._topic: str = Prompt.extract_topic(self._prompt_text)

    def _prepare_prompt_text(self):
        """Fill property from Base Class"""
        return self._prompt_text

    def scan_forest(self):
        """Build Registry with FileTree and RolloutTree of Forest"""
        config: SachmisConfig = get_config()

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

    def models(self) -> list[SproutSelectData]:
        return self._filter_model_select_data_from_sprout_group()

    def _filter_model_select_data_from_sprout_group(self):
        all_models: set[str] = model_uniques()

        model_select_data: list[SproutSelectData] = []

        for sprout_id, sprout_files in self.get_sprout_groups().items():
            self._print_stuff(sprout_id, sprout_files)

            for file in sprout_files:
                printer.title(f"Start of: {file}")

                # Filter if keyword is in models
                if model_unique := file.keywords & all_models:
                    printer.success(f"Found Model: {model_unique=}")
                    if len(model_unique) != 1:
                        raise SachmisDataError("Error in Registry Keywords")
                    data: SproutSelectData = self._create_model_select_data(
                        file, model_unique.pop()
                    )
                    model_select_data.append(data)

        return model_select_data

    def _create_model_select_data(
        self, file: SstFile, model_unique: str
    ) -> SproutSelectData:

        if not (model := model_from_unique(model_unique)):
            raise SachmisDataError(f"Bad Parameter in {file}")

        return SproutSelectData.from_file(
            model=model,
            tree_id=id_keywords_backwards("tree", file.keywords),
            sprout_id=id_keywords_backwards("sprout", file.keywords),
        )

    def _print_stuff(self, sprout_id, sprout_files):  # REMOVE
        printer.special(f"Start of Detected Sprout: {sprout_id}")
        printer([file for file in sprout_files])
        printer.banner("Go")
