from collections import defaultdict
from itertools import product
from pathlib import Path
from typing import Any, Self

from loguru import logger
from sstcore import PathGuard
from sstcore.data import SstFile

from ..config import SachmisConfig, get_config
from ..config.model import ModelFamily
from ..exceptions import (
    ArborealError,
    ArborealFileExistsError,
    SachmisDataError,
    SachmisError,
)
from ..exceptions.data import DataManagerRuntimeError
from ..utils.parse import parse_raw_models
from .arboreal import ArborealTracker, Biome, Forest, Sprout, Tree
from .files import CampManager, UploadFile
from .prompt import Prompt
from .uploader import RemoteUploader, create_uploader


class DataManager:
    """Loads Pydantic models on entry, saves them on clean exit."""

    _camp: CampManager | None = None
    _prompt: Prompt | None = None
    _uploader: dict[str, RemoteUploader] = {}

    _extracted_sprouts: dict[str, ArborealTracker] = {}
    _answer_file_paths: list[Path] = []
    _write_dir_name: str = ""

    # MOVE: to sprout: role as something like Role(SstFile)
    _role_path: Path | None = None
    _role: str | None = None

    @property
    def role_name(self) -> str:  # MOVE: together with role stuff
        return self._role_path.name if self._role_path else "role from text"

    @property
    def camp(self) -> CampManager:
        if self._camp is None:
            raise DataManagerRuntimeError
        return self._camp

    @property
    def prompt(self) -> Prompt:
        if self._prompt is None:
            raise DataManagerRuntimeError("No prompt loaded...")
        return self._prompt

    @property
    def answer_file_paths(self) -> list[Path]:
        """Get the current state of the answer file paths"""
        return self._answer_file_paths

    def get_uploader(self, target: str) -> RemoteUploader:
        if target not in self._uploader:
            self._uploader[target] = create_uploader(target)
        return self._uploader[target]

    def __init__(self, biome=False, forest=False, camp=False):
        """Define at init what is required: Biome, Forest, inside Camp"""
        config: SachmisConfig = get_config()

        self._needs_biome: bool = biome
        self._needs_forest: bool = forest
        self._needs_inside_camp: bool = camp

        if self._needs_biome:
            try:
                self.biome_file: Path = config.paths.biome_file
                logger.debug(f"biome: {self.biome_file}")
            except FileNotFoundError:
                raise ArborealFileExistsError(
                    "Biome", config.paths._biome_file()
                ) from None
            self._full_responses: list[SstFile] = []

        if self._needs_forest:
            self.forest_file: Path = config.paths.forest_file
            logger.debug(f"forest: {self.forest_file}")

        if self._needs_inside_camp:
            self.camp_dir: Path = config.paths.camp_dir_as_parent
            logger.debug(f"camp: {self.camp_dir}")

    def __enter__(self) -> Self:
        logger.info("DataManager: Load data in Context")

        # TASK: Data start?

        return self

    def __exit__(self, exception_type, exception_value, _exception_trace_back):
        logger.info("DataManager: Close data from context")

        # TASK: Exception handling

        if exception_type is not None:
            logger.error(f"DataManager - Error: {exception_type.__name__}")

            if issubclass(exception_type, ArborealError):
                logger.error(f"Context: {exception_value=}")
                logger.warning("State not saved!")
                # Suppress exception (after handling it here)
                return True

            if issubclass(exception_type, SachmisError):
                logger.error(f"SachmisError: {exception_value}")
                logger.warning("State not saved!")
                # Suppress exception (after handling it here)
                return True

            logger.warning("State not saved!")

        if self._extracted_sprouts:
            logger.error("Not all Sprouts arrived well..")
            logger.error(f" No answer from: {self._extracted_sprouts=}")

        if self._needs_biome and self._full_responses:
            self._attach_new_full_responses_to_biome()

        # TASK: Data finish?

        logger.info("DataManager: Clean Exit")

        # Propagate exception to caller
        return False

    def track_extracted_sprout(
        self, sprout: Sprout, tree_tracker: ArborealTracker
    ):
        if not self._needs_forest:
            raise ArborealError("Invalid call for data with forest=False")
        if sprout.unique_id in self._extracted_sprouts:
            raise SachmisDataError("Sprout ID already in registry")

        self._extracted_sprouts[sprout.unique_id] = tree_tracker
        logger.debug(f"linked: {tree_tracker.path.name}, {sprout.unique_id=} ")

    def _attach_sprout_to_tree(self, sprout: Sprout):
        logger.debug("attaching final sprout back to tree")
        tracker: ArborealTracker = self._extracted_sprouts[sprout.unique_id]
        Tree.reattach_sprout(tree_file=tracker.path, sprout=sprout)

    def _attach_new_full_responses_to_biome(self):
        if not self._needs_biome:
            raise ArborealError("Invalid call for data with biome=False")

        config: SachmisConfig = get_config()

        with Biome.edit_mode(config.paths.biome_file) as biome:
            biome.responses.extend(self._full_responses)
            # LATER: clear _full_responses?

        logger.info(f"Attached {len(self._full_responses)} files to Biome")

    def _add_temporary_full_response(self, text: str, path: Path) -> None:

        path.write_text(text)
        response: SstFile = SstFile(local_path=Path(path.name))

        self._full_responses.append(response)

    def load_prompt(
        self, source: str | Path | None = None, topic: str | None = None
    ) -> Prompt:
        if isinstance(source, str):
            self._prompt: Prompt = Prompt.load_from_text(source, topic)
            self._input_prompt_path: Path | None = None
        else:
            config: SachmisConfig = get_config()
            path: Path = source or Path(config.names.prompt)
            self._prompt: Prompt = Prompt.load_from_path(path, topic)
            self._input_prompt_path: Path | None = path

        self._prompt_written = False

        return self._prompt

    def load_camp(self, forest: Forest):
        self._camp: CampManager = forest.provide_camp()

    def load_files(self, files: list[UploadFile], ensure_after_upload=True):
        """Assumes valid local data files, pushes to Remotes"""

        logger.debug("attaching files to data.prompt")

        prompt_files: list[UploadFile] = self.prompt.files

        for file, uploader in product(files, self._uploader.values()):
            try:
                uploader.upload_local_file(file, ensure_after_upload)
                prompt_files.append(file)
            except FileNotFoundError:
                logger.error(f"Missing {file=}")
            except RuntimeError as err:
                logger.error(f"Upload failed {file=}, {err}")
                # TODO: check if raise or not

    def load_images(self, images: list[SstFile]):
        """Assumes valid local image files, pushes to Remotes"""

        logger.debug("attaching files to data.image")

        prompt_files: list[SstFile] = self.prompt.images
        # TODO: any checks, logs, or prints?

        prompt_files.extend(images)

    def load_role(self, role_path: Path | None = None):
        if role_path is not None and (role := role_path.read_text()):
            self._role_path: Path | None = role_path
            self._role: str | None = role

    ### --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    ### --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

    def scan_dir_for_models(self):
        """Scan file system for existing conversation"""
        config: SachmisConfig = get_config()

        self._scanned_models: dict[str, list[dict[str, str]]] = defaultdict(
            list
        )
        self._next_fs_locator: int = 0

        if Path.cwd() == config.paths.base_dir:
            logger.debug("located in top folder, attach 0")
            self._write_dir_name: str = self.prompt.topic  # IDEA: tree name?
            return

        for path in Path.cwd().glob("*.md"):
            try:
                parts: dict[str, str] = config.names.sprout_stem(path.stem)
            except ValueError:
                continue
            if (model_unique := parts["spec"]) == "prompt":
                continue
            self._scanned_models[model_unique].append(parts)

        for model, files in self._scanned_models.items():
            for name_parts in files:
                locator_num = int(name_parts["locator"])
                if locator_num >= self._next_fs_locator:
                    self._next_fs_locator: int = locator_num + 1
            logger.debug(f"default attach to {locator_num=} of {model=}")

    def parse_scanned_models(self) -> list[ModelFamily]:
        return parse_raw_models(list(self._scanned_models.keys()))

    def neighbours_formated(self, model_name: str) -> dict[str, str]:
        sprouts: list[dict[str, str]] = self._scanned_models[model_name]

        def _format(sprout: dict[str, str]) -> str:
            return f"{model_name} - {sprout['locator']} - {sprout['topic']}"

        return {sprout["locator"]: _format(sprout) for sprout in sprouts}

    def set_file_system_locator(self, locator: str, model_name: str):
        config: SachmisConfig = get_config()

        locations: list[dict[str, str]] = self._scanned_models[model_name]
        for location in locations:
            if location["locator"] == locator:
                name_parts: dict[str, str] = location
                break
        else:
            raise SachmisDataError(f"Failed to find {locator=}")

        sub_locator = 1

        for path in Path.cwd().glob(f"_{locator}*_{model_name}"):
            _dom, loc, _spec, _topic = config.names.sprout_stem(path.stem)
            splitted: list[str] = loc.split(".")  # PARAM: symbol for locator
            if splitted[0] != locator and len(splitted) != 2:
                raise SachmisDataError(f"Bad locator: {loc} for {locator}")
            if sub_locator <= (existing_sub := int(splitted[1])):
                sub_locator: int = existing_sub + 1

            # TODO: other name
            new_locator: str = f"{name_parts['locator']}.{sub_locator}"
            name_parts["locator"] = new_locator

        self._write_dir_name: str = config.names.sprout_stem(name_parts)
        self._next_fs_locator: int = 1

    def set_model_subdir(self, model_name: str):

        match len(paths := list(Path.cwd().glob(f"_{model_name}_"))):
            case 0:
                raise SachmisDataError("No path to create Model subgroup")
            case 1:
                model_path: Path = paths[0]
            case _:
                raise SachmisDataError(
                    "Multiple paths to create Model subgroup"
                )
        self._write_dir_name: str = model_path.stem
        self._next_fs_locator: int = 1

    ### --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    ### --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

    def _move_and_write_prompt(self, prompt_path: Path):
        config: SachmisConfig = get_config()

        if self._input_prompt_path is None:
            prompt_path.write_text(self.prompt.text)
        else:
            PathGuard.rotate(
                source=self._input_prompt_path, target=prompt_path, reset=True
            )
            if self._write_dir_name:
                prompt_path.with_name(config.names.prompt).touch()

        logger.debug(f"prompt moved: {prompt_path=}")

    def handle_response(self, sprout: Sprout):
        """So far: write when desired, later handle filetree | other.."""
        config: SachmisConfig = get_config()

        if sprout.response is None:
            logger.error(f"Can't process empty response of {sprout=}")
            return

        path_args: dict[str, Any] = {
            "topic": sprout.prompt.slug_topic,
            "locator": f"{self._next_fs_locator}",
            "root_dir": (Path.cwd() / self._write_dir_name),
        }

        answer_path: Path = config.paths.answer_file(
            model=sprout.model, **path_args
        )
        answer_path.write_text(sprout.response.content)
        self._answer_file_paths.append(answer_path)

        if not self._prompt_written:
            prompt_path: Path = config.paths.prompt_file(**path_args)
            self._move_and_write_prompt(prompt_path)
            self._answer_file_paths.append(prompt_path)
            self._prompt_written = True

        logger.info(f"Response written to: {answer_path=}")
