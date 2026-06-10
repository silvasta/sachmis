from contextlib import AbstractContextManager, ExitStack
from typing import Self

from loguru import logger

from sachmis.data.conversation.fusion import SproutPackage

from ..config import SachmisConfig, get_config
from ..config.defaults import ModelParam
from ..config.models import DummyFamily, Geminis, Groks
from ..data import DataManager
from ..data.conversation import SelectedSproutData
from ..data.handler import FileRollout
from .context import ForestExtractor, TreeExtractor
from .model import Gemini, Grok, Model, launch
from .model.dummy import DummyModel
from .sprout import Sprout

config: SachmisConfig = get_config()


def load_model(
    model, sprout: Sprout, param: ModelParam | None = None
) -> Model:
    """Create Execution Model from Enum Family Model"""

    if isinstance(model, Groks):
        sprout.data.uploader.prepare(target=model.target)
        return Grok(model, sprout, param)

    if isinstance(model, Geminis):
        sprout.data.uploader.prepare(target=model.target)
        return Gemini(model, sprout, param)

    if isinstance(model, DummyFamily):
        return DummyModel(model, sprout, param)

    raise ValueError(f"Unknown {model=}")


class Fire(AbstractContextManager):
    def __init__(self):
        self.stack: ExitStack = ExitStack()
        self.agents: list[Model] = []

    def __enter__(self) -> Self:
        self.data: DataManager = self.stack.enter_context(
            DataManager(handler=FileRollout())
        )
        self.forest: ForestExtractor = self.stack.enter_context(
            ForestExtractor(self.data)
        )
        logger.info("ForestExtractor: Stacked to Context")

        self.tree: TreeExtractor = self.stack.enter_context(
            TreeExtractor(data=self.data)  # MOVE: after selection?
        )
        logger.info("TreeExtractor: Stacked to Context")

        logger.success("capstone.Fire session is ready")
        return self

    def load_models(self, models: list[SelectedSproutData]) -> list[Model]:
        logger.info(f"Start of loading: {models=}")

        self.agents: list[Model] = []

        for model in models:
            package: SproutPackage = self.data.handler.prepare_package(model)

            sprout = Sprout(package, self.data)

            load_model(model, sprout)

        logger.info(f"Loaded: {self.agents=}")

        return self.agents

    def launch(self, use_async=False, dry_run=False):
        launch.models(self.agents, use_async, dry_run)

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.stack.__exit__(exc_type, exc_val, exc_tb)
