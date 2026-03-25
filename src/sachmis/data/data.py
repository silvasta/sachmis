from pathlib import Path
from typing import Literal

from loguru import logger

from ..utils.image import load_b64_and_encode, load_bytes_image
from ..utils.pick import pick_role
from ..utils.print import printer
from .uploader import FileUploader, GoogleUploader, XaiUploader


class DataManager:
    """Handles data of {1 or multiple} {task|model}{s} and file system"""

    chat_topic: str | None = None
    prompt: str | None = None  # readed once for all models
    topic: str | None = None  # calculated from prompt

    input_prompt_path: Path | None = None
    answer_paths: list[Path] = []  # storage for final display

    input_image_paths: list[Path] = []  # path to regular image files
    base64_images: list[str] = []  # base64 strings of images used for Grok
    bytes_images: list[bytes] = []  # base64 strings of images used for Grok

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

        full_response_path: Path = self.write_full_response(
            full_response, stem
        )
        logger.debug(f"Full response written to: {full_response_path=}")

        answer_path: Path = self.write_content(content, stem=stem)
        logger.debug(f"Content written to: {answer_path=}")
        self.answer_paths.append(answer_path)

        printer.md("Content written to:", H=3, style="write")
        printer.print(answer_path.name)

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
        answer_path: Path = PathGuard.unique(
            self.config.answer_file_path(stem=stem)
        )
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
