import random
from pathlib import Path

from sstcore import PathGuard
from sstcore.utils import (
    setup_logging,
)
from sstcore.utils.parse import ParsedName

from sachmis.config import SachmisConfig, get_config
from sachmis.config.models import select
from sachmis.config.names import (
    PromptNameSchema,
    ResponseNameSchema,
    TreeNameSchema,
)
from sachmis.utils.print import printer

config: SachmisConfig = get_config()

_test_dir_root = config.paths.project_root / "tests/path_tree/exp"

_tree_parser: ParsedName[TreeNameSchema] = config.names.tree_parser
_prompt_parser: ParsedName[PromptNameSchema] = config.names.prompt_parser
_answer_parser: ParsedName[ResponseNameSchema] = config.names.response_parser

setup_logging(log_level_override="WARNING")


def main():
    printer.title("Start")
    create_test_directory_1()


def _promt_response(path):
    printer.danger(["Prompt scans response:", path])
    for neighbour in path.parent.iterdir():
        if _answer_parser(neighbour):
            printer.header(["Found Neighbour", neighbour], frame="purple")


def _promt_tree(path):
    if _tree_data := _tree_parser(_rel(path).parts[1]):
        printer.success("found tree")
        printer(_tree_data)
    else:
        printer.danger("no tree")


def create_test_directory_1():
    printer(test_dir())
    _t1_mixed_1 = attach_with_tree_in_root(models=random_models(5))
    _t2_mixed_2 = attach_with_tree_in_root(models=random_models(3))
    _t3_single_1 = attach_with_tree_in_root(models=random_models(1))
    _t4_single_2 = attach_with_tree_in_root(models=random_models(1))

    _t1_1_next_multi = ""


def attach_with_tree_in_root(models) -> Path:
    topic = TREES[tree_counter]

    tree = create_tree(topic)
    tree_root: Path = PathGuard.dir(test_dir() / tree)
    printer.success(f"Created: {tree_root.name}")
    _all: list[Path] = [_rel(tree_root)]

    sprout: list[str] = create_sprout(topic, models)
    _all += [_rel(_file(tree_root / f"{s}.md")) for s in sprout]
    printer.lines_with_len(name="Tree and Sprouts", lines=_all)

    return tree_root


_test_dir: Path | None = None


def test_dir() -> Path:
    global _test_dir
    if _test_dir is None:
        _raw = _test_dir_root / "forest"
        _test_dir = PathGuard.unique(_raw, ensure_parent=True)
    return _test_dir


def _file(path: Path) -> Path:
    return PathGuard.file(path, default_content="", raise_error=False)


def _rel(target: Path) -> Path:
    return PathGuard.relative(target, root=_test_dir_root)


# def find():
#     # Create the filter using your fully-typed Pydantic factory
#     tree_filter = StemFilter(parser=names.tree_parser, _debug=True)
#
#     # Walk the directory. It will safely skip .git/.venv and ONLY yield valid Tree files.
#     for tree_file in FolderScanner.walk(
#         root=base_dir, path_filter=tree_filter
#     ):
#         # Because it passed the filter, you are guaranteed that this won't throw an error:
#         tree_data = names.tree_schema(tree_file)
#         print(f"Found Tree {tree_data.id}: {tree_data.topic}")

### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### TREE, SPROUT, ID
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --


tree_counter = 0


def tree_id() -> int:
    global tree_counter
    tree_counter += 1
    return tree_counter


def create_tree(topic) -> str:
    tree_stem: str = _tree_parser((tree_id(), topic))
    return tree_stem


sprout_counter = 0


def sprout_id() -> int:
    global sprout_counter
    sprout_counter += 1
    return sprout_counter


def create_sprout(topic, models: list[str]) -> list[str]:
    id = sprout_id()
    return [
        _prompt_parser((id, topic)),
        *[_answer_parser((id, model, topic)) for model in models],
    ]


### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### MODELS
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --

all_models: list[str] = [
    model.unique for model in select(dummy=True, grok=False, gemini=False)
]


def random_model_index():
    return random.randint(0, len(all_models) - 1)


def random_models(num=1) -> list[str]:
    return list(set(all_models[random_model_index()] for _ in range(num)))


### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### DATA
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --

TREES: list[str] = [
    "alpha",
    "beta",
    "gamma",
    "delta",
    "epsilon",
    "zeta",
]

SPROUTS: list[str] = [
    "The quick brown fox jumps over the lazy dog.",
    "A journey of a thousand miles begins with a single step.",
    "Testing the water before jumping in.",
    "Short title.",
    "A significantly longer string to ensure that the user interface layout doesn't break.",
    "Just another random test sentence.",
    "Coffee is an essential part of the morning routine.",
    "The sun sets in the west every evening.",
    "Data validation is crucial for robust applications.",
    "Hello, World!",
    "Lorem ipsum dolor sit amet.",
    "Checking edge cases and boundary conditions.",
    "Apples and oranges are both delicious fruits.",
    "Sometimes the simplest solution is the best one.",
    "Can this field handle special characters like !@#$?",
    "Numbers 1234567890 should work fine too.",
    "The silent cat stalks the red laser pointer.",
    "Walking through the forest brings peace of mind.",
    "This is a standard placeholder sentence for testing.",
    "Almost halfway through the test data array.",
    "Is it raining outside today?",
    "The cake is a lie.",
    "User interface design requires empathy and patience.",
    "Backend systems need to be scalable and secure.",
    "Continuous integration saves hours of debugging time.",
    "A clear blue sky usually means excellent weather.",
    "Reading the documentation is always highly recommended.",
    "Debugging is like being the detective in a crime movie where you are also the murderer.",
    "Music helps many developers focus better on their code.",
    "Another completely random thought for the database.",
    "The automated test script ran successfully.",
    "Please ensure all required fields are filled out correctly.",
    "An unexpected error occurred on line 42.",
    "The database connection was established successfully.",
    "How does the system handle unexpected inputs?",
    "Water boils at one hundred degrees Celsius.",
    "Programming is considered both an art and a science.",
    "A stitch in time saves nine.",
    "Keep your friends close, but your test data closer.",
    "Actions speak louder than words in software development.",
    "The keyboard is mightier than the sword.",
    "This is the final test sentence in the array.",
]

if __name__ == "__main__":
    main()
