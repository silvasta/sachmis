from pathlib import Path
from typing import Literal, Any

from .uploader import GoogleUploader, XaiUploader, FileUploader
from boltons.strutils import slugify
from loguru import logger
from rich.table import Table

from ..utils.config import ConfigManager
from ..utils.image import load_b64_and_encode, load_bytes_image
from ..utils.path import PathGuard
from ..utils.pick import pick_role
from ..utils.print import printer
from .forest import Forest, Tree, File
from .models import Models


class DataManager:
    """Handles data of {1 or multiple} {task|model}{s} and file system"""

    chat_topic: str | None = None
    config: ConfigManager  # loaded at init
    forest: Forest  # loaded before model preparation
    prompt: str | None = None  # readed once for all models
    topic: str | None = None  # calculated from prompt

    input_prompt_path: Path | None = None
    answer_paths: list[Path] = []  # storage for final display

    input_image_paths: list[Path] = []  # path to regular image files
    base64_images: list[str] = []  # base64 strings of images used for Grok
    bytes_images: list[bytes] = []  # base64 strings of images used for Grok

    files: list[File] = []

    def __init__(self, config: ConfigManager | None = None):
        self.config: ConfigManager = config or ConfigManager()
        logger.info("DataManager setup completed")

    def create_new_base(
        self,
        base_name: str | None = None,
        prompt_name: str | None = None,
        camp_name: str | None = None,
    ):
        """Setup local folder for conversations, loops and trees"""
        logger.info("Creating new base")

        # NOTE: avoid creating base in base?

        base_name: str = base_name or self.config.base_name
        base_path: Path = PathGuard.dir(Path.cwd() / base_name)

        camp_name: str = camp_name or self.config.camp_name
        camp_path: Path = PathGuard.dir(base_path / camp_name)
        # TODO: camp installation
        # - create folders for image, but from config, probably move cwd
        # - local config and roles

        prompt: Path = base_path / self.config.default_prompt_name
        prompt.touch()

        printer.success("Paths and files reads, creating Forest now")
        forest = Forest(tree_file_path=base_path / self.config.forest_file_name)
        forest.save_state()

        printer.success(f"New base created! {base_path=}")
        self.append_new_base_to_list(camp_path)

    def append_new_base_to_list(self, camp_path: Path):
        """Log base- and camp name, so far to regular log file"""
        logger.info(f"{self.config.new_base_tag}: {camp_path}")

    # NOTE: base list: process log file or save better

    def show_all_bases(self):
        """load base paths from file, check existance, print result"""
        file_path: Path = self.config.log_file_path

        if not file_path.is_file():
            logger.error(f"No file found at: {file_path}")
            printer.fail("Base List file is missing...")
        else:
            table = Table(title="Distributed Bases")
            table.add_column("Status", justify="center")
            table.add_column("Base", style="cyan")
            with open(file_path, "r") as f:
                tag: str = self.config.new_base_tag
                while line := f.readline():
                    if tag in line:
                        raw_path: str = line.split(f"{tag}:")[-1].strip()
                        base_path = Path(raw_path)
                        status: str = "✅" if base_path.is_dir() else ""
                        table.add_row(status, str(base_path))
            printer.print(table)

    def show_forest(
        self,
        mode: Literal["tree", "loaded", "files"],
        select: dict[str, list[str]] | None = None,
    ):
        """Save load forest, print as tree or json file"""
        try:
            self.load_forest()
        except Exception as e:
            printer.title("There is no forest around...\nnot even a tree")
            logger.error(e)
        match mode:
            case "tree":
                printer.forest(self.forest)
            case "loaded":
                printer.print(self.forest)
            case "order":
                printer.title("File Category")
                printer.print(self.forest.file_categories)
                printer.title("File Topic")
                printer.print(self.forest.file_topics)
            case "files":
                files: list[File] = self.forest.file_selection(
                    categories=select.get("category") if select else None,
                    topics=select.get("topic") if select else None,
                )
                printer.title(f"File Selection ({len(files)} files)")
                for file in files:
                    printer.print(file.description)

    def load_forest(self):
        """Load forest to class atribute If inside tree environment"""
        if self.config.forest_file is None:
            logger.error(f"No forest or tree to show at: {Path.cwd()}")
            raise FileNotFoundError("Not in forest environment, no tree around!")
        else:
            logger.info(f"Loading tree from: {self.config.forest_file}")
            # HACK: use somehow contextmanager and close/save automatically at the end
            self.forest: Forest = Forest.load_state(self.config.forest_file)
            if self.config.in_camp:
                logger.debug("in_camp -> no root tree")
                self.local_root_tree = None
            else:
                logger.debug("start finding root tree")
                self.local_root_tree: Tree | None = self.forest.find_local_root_tree()

    def load_files_to_forest(self, from_empty_status=False, sort="section"):
        self.load_forest()
        logger.info(f"Forest has {len(self.forest.files)} files before")

        self.forest.update_files(
            self.config.file_dir,
            sort,
            from_empty_status,
        )
        logger.info(f"Forest has now {len(self.forest.files)} files")
        self.forest.save_state()

    def manage_online_forest_files(
        self,
        xai=False,
        google=False,
        task: Literal["push", "show", "delete"] = "show",
    ):
        self.load_forest()

        uploaders: list[FileUploader] = []
        if xai:
            uploaders.append(XaiUploader())
        if google:
            uploaders.append(GoogleUploader())

        for uploader in uploaders:
            match task:
                case "push":
                    for file in self.forest.files:
                        # NOTE: use this during runtime, e.g. in Fire or Script
                        uploader.upload_local_file(file, base_path=self.config.file_dir)
                case "show":
                    uploader.show_all_files()
                case "delete":
                    uploader.delete_all_uploaded_files()

        self.forest.save_state()

    def tree(self, sprout_path: Path):
        """Create new sprout, transform local tree into root of new subfolder"""

        sprout: Tree | None = self.forest.find_tree_by_path(sprout_path)

        if sprout is None:
            logger.error(f"No tree_stem match for {sprout_path=}")
            printer.fail("No tree found as sprout... ")
            return
        printer.success("Found local tree")

        sprout_root = Path(sprout.tree_stem)
        PathGuard.dir(sprout_root)

        prompt: Path = sprout_root / self.config.default_prompt_name
        prompt.touch()

        PathGuard.rotate(
            sprout_path,
            sprout_root / sprout_path.name,
            reset=False,
        )  # NOTE: no changes at Tree or Forest object itself, only file system location changed

    def load_prompt(self, prompt_path=None, prompt_text: str | None = None):
        """Load prompt in storage, Priority: text > path > read from file"""
        if prompt_text is not None:
            prompt: str = prompt_text
            logger.debug("using prompt from prompt_text")
        else:
            self.input_prompt_path: Path = (
                Path.cwd() / self.config.default_prompt_name
                if prompt_path is None
                else prompt_path
            )
            prompt: str = self.input_prompt_path.read_text()
            logger.debug(f"using prompt from {self.input_prompt_path=}")

        lines: list[str] = prompt.splitlines()
        try:
            first_non_empty: str = next(line.strip() for line in lines if line.strip())
            self.topic: str = slugify(first_non_empty, delim="-")
            self.prompt: str = prompt
            logger.info(f"Prompt loaded, topic is: {self.topic}")
        except StopIteration:
            self.topic = None
            self.prompt = None
            logger.error("Prompt is empty, fix that before model release!")

    def prepare_images(self, images: list[Path]):
        """Assume forest and prompt loaded, extend data with image,..."""
        for image in images:
            if not image.is_file():
                logger.warning(f"Invalid image path: {image}")
                continue
            self.load_input_image(image)
        # if len(images) > 0:
        #     logger.info(f"Use {len(self.input_images)} out of {len(images)} images")

    def load_input_image(self, image_path: Path) -> None:
        """So far, encoding image to base64 string"""

        # b64 string images loading for grok
        if image := load_b64_and_encode(image_path):
            self.base64_images.append(image)
        else:
            logger.warning(f"Base 64 image loading failed: {image_path}")

        # bytes image loading for gemini
        if image := load_bytes_image(image_path):
            self.bytes_images.append(image)
        else:
            logger.warning(f"Bytes image loading failed: {image_path}")

        self.input_image_paths.append(image_path)

    def prepare_files(self, file_names: list[str]):
        n_input_files: int = len(file_names)

        selected_files: list[File] = [
            file for file in self.forest.files if file.name in file_names
        ]
        # TODO: print this somewhere (as function, not here)
        # for file in self.forest.files:
        #     printer.print(file)

        n_selected: int = len(selected_files)
        self.files.extend(selected_files)

        if n_selected == n_input_files:
            logger.info(f"Attached all {n_input_files} files from registry to data")
        else:
            logger.warning(f"Attached Only {n_selected} out of {n_input_files} files!")

    def load_system_role(self, role_path: Path | None = None) -> None:
        """Role text overrides paths if provided"""
        self.role_path: Path = role_path or pick_role(path=self.config.role_dir)
        self.system_role: str = self.role_path.read_text()

    def get_previous_id(self, model: Models) -> str | None:
        """Return previous ID only for same class of Models"""
        logger.debug("start get_previous_id")
        if self.local_root_tree is None:
            logger.debug("no local_root_tree -> no previous_id")
            return None

        previous_model: str = self.local_root_tree.model

        if previous_model == model.unique:
            logger.debug(f"Match!{previous_model=} == {model=}")
            return self.local_root_tree.id
        else:
            logger.debug(f"No match!{previous_model=} != {model=}")
            return None

    def process_response(
        self,
        id: str,
        model: Models,
        usage: dict[str, int],
        content: str,
        full_response: str,
        topic: str | None = None,
    ):
        # ignores None and "" and 0, usually danderous, here useful
        topic: str = topic or self.topic or "topic-is-None"
        # TASK: new conversation setup
        # - conversation with entire dialog
        # - files! used and with which status
        stem: str = self.config.tree_stem(
            topic=topic,
            characteristic=model.unique,
        )

        full_response_path: Path = self.write_full_response(full_response, stem)
        logger.debug(f"Full response written to: {full_response_path=}")

        answer_path: Path = self.write_content(content, stem=stem)
        logger.debug(f"Content written to: {answer_path=}")
        self.answer_paths.append(answer_path)

        printer.md("Content written to:", H=3, style="write")
        printer.print(answer_path.name)

        # NEXT: save response in Forest in Tree
        save_content = None

        if self.local_root_tree is None:  # root folder
            previous_id: str = ""
        else:
            previous_id: str = self.local_root_tree.id

        # NOTE: protect failures here?
        self.forest.trees[id] = Tree(
            id=id,
            model=model.unique,
            tree_stem=stem,
            ancestor=previous_id,
            usage=usage,
            full_response_path=full_response_path,
            content=save_content,
        )
        logger.info(f"Added tree number {len(self.forest.trees)=} with {id=}")
        # NOTE: something better than saving the entire tree always?
        self.forest.save_state()

    def write_full_response(self, response: str, stem: str) -> Path:
        full_response_path: Path = self.config.full_response_path(stem=stem)
        full_response_path.write_text(response)
        return full_response_path

    def write_content(self, content: str, stem: str) -> Path:
        answer_path: Path = PathGuard.unique(self.config.answer_file_path(stem=stem))
        answer_path.write_text(content)
        return answer_path

    def rotate_prompt(self, new_prompt_path):
        """Handle prompts in setup with 1 prompt and 1+ answer"""
        if self.input_prompt_path:
            PathGuard.rotate(
                source=self.input_prompt_path,
                target=new_prompt_path,
                reset=True,
            )
        else:
            logger.error("Nothing to rotate!")

    def write_prompt(self, new_prompt_path: Path):
        """Handle prompts in setup with multiple prompts"""
        if self.prompt:
            new_prompt_path.write_text(self.prompt)
            logger.debug("prompt written to new file")
        else:
            logger.error("Nothing to write as Prompt!")

    def handle_prompt(self):
        new_prompt_path: Path = self.config.prompt_file_path(topic=self.topic)
        if self.input_prompt_path is None:
            logger.debug("no input_prompt_path -> write_prompt")
            self.write_prompt(new_prompt_path)
        else:
            logger.debug("input_prompt_path -> rotate_prompt")
            self.rotate_prompt(new_prompt_path)

    def process_files(self):
        """This is for setup with 1 prompt and 1+ answer"""

        logger.info("Writing forest")
        self.forest.save_state()

        self.handle_prompt()
        logger.info("Prompt placed at new location")

        printer.title("Answer Paths", style="warning")
        for path in self.answer_paths:
            printer.print(Path(path.name), style="warning")
