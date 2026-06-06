from enum import StrEnum, auto
from pathlib import Path

from sstcore import PathGuard
from sstcore.config import ParsedName
from sstcore.utils.print import ColorBox

from sachmis.config.models import ModelFamily

from ..config import SachmisConfig, get_config
from ..config.models import all
from ..utils import printer

config: SachmisConfig = get_config()

c: ColorBox = ColorBox()
c._colors.black = "dark_goldenrod"

text = f"{c.black('TreeIDMissingError')} Important for the Order!"


class Status(StrEnum):
    DEFAULT = auto()
    ROOT = auto()

    @property
    def action(self) -> bool:
        return self in {self.DEFAULT, self.ROOT}

    def models(self, pick_model) -> list[ModelFamily]:
        printer(f"{pick_model=}")
        match self:
            case self.DEFAULT | self.ROOT:
                return all()


class FileRollout:
    """Manage Prompt and Response write to Forest dir"""

    topic: str = ""
    tree_id = 0
    sprout_id = 0
    status: Status = Status.DEFAULT

    tree_stem: ParsedName
    sprout_stem: ParsedName

    neighbours: dict[str, dict] = {}  # {id : parsed_dict}

    result_files: list[Path] = []

    def __init__(self):

        tree_stem_pattern: str = config.names.tree_file.rstrip(".json")
        self.tree_stem = ParsedName(pattern=tree_stem_pattern)
        self.sprout_stem = ParsedName(pattern=config.names.sprout_stem)

        relative_to_base: Path = config.paths.cwd_to_base_dir()
        printer.title(relative_to_base, frame="purple", title="relative")
        printer.title(_cwd := Path.cwd(), frame="purple", title="cwd")

        if relative_to_base == Path():
            self.status: Status = Status.ROOT
        else:
            self.extract_id(tree_stem=relative_to_base.parts[0])

        self.analyze_cwd()
        self.analyze_neighbours()

    def analyze_neighbours(self):
        pass

    # TASK: cases:
    # - 0 -> select from All
    # - multiple but ancestors, no select
    # - multiple Select from Subset
    # match len(self.neighbours):
    #     case 0:
    #         pass
    #     case 1:
    #         pass
    #     case _:
    #         pass

    def extract_id(self, tree_stem):
        tree_name_parts: dict = self.tree_stem(tree_stem)
        printer.success(f"{tree_name_parts=}")
        self.tree_id = int(  # WARN: maybe no or parsed int
            tree_name_parts["id"]
        )

    def analyze_cwd(self):
        for path in Path.cwd().iterdir():
            self._parse(path, self.tree_stem)
            self._parse(path, self.sprout_stem)
        printer.magenta(f"Found {len(self.neighbours)} neighbours")

    def _parse(self, path, name_parser_function: ParsedName):
        try:
            if result := name_parser_function(path):
                if isinstance(result, dict):
                    printer.dict_table(result)
                else:  # TODO: extract
                    printer.header(result, frame="purple")
        except (ValueError, KeyError) as error:
            printer.danger(f"Problems while Parsing: {c.red(f'{error=}')}")

    def process(self, model, topic, sprout_id, tree_id=0):

        if self.status.ROOT and not tree_id:
            printer.header(text, frame="orange_red1")

        sprout_args: list = [sprout_id, model.unique, topic]
        sprout_stem: str = self.sprout_stem(sprout_args)

        if self.status == Status.ROOT:  # TODO:FLAG AGAINST REPEAT
            tree_stem: str = self.tree_stem([self.tree_id, self.topic])
            dir: Path = PathGuard.dir(tree_stem)
            path: Path = dir / sprout_stem

        else:  # WARN: Folder change status, figure out!
            path: Path = Path(sprout_stem)
        path.write_text("hello")
