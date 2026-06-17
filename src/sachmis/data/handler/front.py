from enum import StrEnum, auto
from pathlib import Path

from loguru import logger
from sstcore import PathGuard
from sstcore.data import SstFile

from sachmis.data.files.front import FrontFileRegistry

from ...config import SachmisConfig, get_config
from ...config.models import uniques as model_uniques
from ...config.names import id_keywords_backwards
from ...exceptions import SachmisDataError, SachmisLaunchError
from ...utils import model_from_unique, printer
from ..conversation import Prompt, Response, SproutSelectData


class Status(StrEnum):
    """Status of CWD Folder and Files"""

    # NEXT: define status

    UNDEFINED = auto()
    ROOT = auto()
    SINGLE = auto()
    LONG = auto()
    CROWD = auto()


class FrontFileHandler:
    """Manage Prompt and Response write to Forest dir"""

    status: Status = Status.UNDEFINED
    _result_files: list[Path] = []
    write_dir: Path = Path.cwd()

    scanned_tree_id: int = 0
    _prompt_text: str = ""
    _topic: str = ""

    @property
    def topic(self):
        """Ensure Handler has loaded a valid topic"""
        if not (topic := self._topic):
            name: str = self.__class__.__name__
            SachmisDataError(f"{name} has no valid Prompt Topic!")
        return topic

    @property
    def result_file_paths(self) -> list[Path]:
        """Provide absolute Paths of already written result files"""
        return self._result_files

    def result_files_relative(
        self,
        root_dir: Path | None = None,
    ) -> list[Path]:
        """Provide relative Paths of already written result files"""
        return list(
            PathGuard.relative(target=path, root=root_dir, strict=False)
            for path in self._result_files
        )

    def __init__(self):
        self._load_prompt_text()
        self.scan_forest()
        self._print_for_init()

    def _print_for_init(self):  # NEXT: clean entry prints
        config: SachmisConfig = get_config()
        if not config.paths.in_forest:
            printer.danger("Outside Forest Dir!")
        else:
            relative_to_base = config.paths.cwd_to_base_dir()
            printer.title(f"Location: {relative_to_base=}", frame="purple")

    def _load_prompt_text(self):
        config: SachmisConfig = get_config()

        self.input_prompt_path: Path = config.paths.input_prompt
        # FIX: no PathGuard.file if wrong directory!
        logger.info(f"Loading prompt text from: {self.input_prompt_path=}")

        self._prompt_text: str = self.input_prompt_path.read_text()
        self._topic: str = Prompt.extract_topic(self._prompt_text)
        logger.info(f"Loaded prompt with Topic: {self.topic}")

    def scan_forest(self):
        """Build Registry with FileTree of Forest Front View Files"""
        config: SachmisConfig = get_config()

        self.registry: FrontFileRegistry = FrontFileRegistry.ready()

        if (tree_schema := self.registry.find_tree_above()) is None:
            if not config.paths.cwd_in_top_dir:
                raise SachmisLaunchError("Bad Location, Sprout has not Tree!")
            self.scanned_tree_id = 0
        else:
            self.scanned_tree_id: int = tree_schema.tree_id

    def get_sprout_groups(self) -> dict[str, list[SstFile]]:
        # MOVE: to registry
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

        printer.debug("Detect Model", all_models, model_select_data, bare=True)

        for sprout_id, sprout_files in self.get_sprout_groups().items():
            printer.debug(f"Detected Sprout: {sprout_id}", sprout_files)

            for file in sprout_files:
                printer.title(f"Start of: {file}")

                # Filter if keyword is in models
                if model_unique := file.keywords & all_models:
                    logger.debug(f"Found Model: {model_unique=}")
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

        logger.debug(f"Creating ModelSelectData for {model_unique}: {file=}")

        printer.debug("Create Model Select Data", model_unique, file)

        if not (model := model_from_unique(model_unique)):
            raise SachmisDataError(f"Bad Parameter in {file}")

        return SproutSelectData.from_file(  # NEXT: rename: ModelSelectData
            model=model,
            tree_id=id_keywords_backwards("tree", file.keywords),
            sprout_id=id_keywords_backwards("sprout", file.keywords),
        )

    def handle_response(self, response: Response):
        config: SachmisConfig = get_config()
        logger.info(f"Handling {response=}")

        # REMOVE:
        self.response = response

        if self.status == Status.UNDEFINED:
            # TASK: check usage or need for Status???
            # - maybe outsource Actions to that
            self._check_cwd_and_tasks()
            self.rotate_prompt(response.sprout_id, response.topic)

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
            return

        models: set[str] = self.registry.get_model_at_path()

        if len(models) == 1:  # WARN: ignores multitple of same model
            self.status: Status = Status.SINGLE
            self.action_chain()
        # TASK: dispatch for long
        #  case Status.LONG:
        #     if self.has_selected:
        #         self.action_dig()
        #       else: stay()?
        else:
            self.status: Status = Status.CROWD
            self.action_dig()

    def rotate_prompt(self, sprout_id: int, topic: str):
        # TODO: self.topic or topic? drop at least 1
        config: SachmisConfig = get_config()
        prompt_path: Path = config.paths.prompt_file(
            self.write_dir, sprout_id, topic
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

        tree_stem: str = config.names.tree_stem(
            self.response.tree_id, self.response.topic
        )
        printer(tree_stem)
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
            self.response.sprout_id,  # FIX: previous sprout_id!!
            self.response.model,
            self.response.topic,
        )
        self.write_dir: Path = PathGuard.dir(previous_stem)
        logger.info(f"Target Dir created: {previous_stem}")
