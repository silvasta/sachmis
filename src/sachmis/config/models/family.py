import uuid
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from enum import Enum, EnumMeta
from typing import Self

from sstcore.utils.print import ColorBox

# INFO: this is the Model Param Schema for fixed external data

# REFACTOR: Use csv/pyandtic instead of Enum?
# - still nice with Enum, match and validation
# - maybe basemodel just for data?

# LATER: load family from csv
# - load including prices, status=Active etc,
# check file-analyzer for template pydantic read/write


c = ColorBox()


@dataclass
class ModelSelectData:
    uuid: str
    show: str
    model: ModelFamily
    tree_id: int = 0
    sprout_id: int = 0

    @classmethod
    def from_model(cls, model: ModelFamily) -> Self:
        return cls(uuid=str(uuid.uuid4()), show=model.id_cli, model=model)

    @classmethod
    def from_data(cls, model: ModelFamily, tree_id, sprout_id) -> Self:
        return cls(
            uuid=str(uuid.uuid4()),
            show=model.id_cli,
            model=model,
            tree_id=tree_id,
            sprout_id=sprout_id,
        )

    @classmethod
    def fresh_models(cls, models: list[ModelFamily]) -> list[Self]:
        return [cls.from_model(model) for model in models]


class AbstractEnum(ABCMeta, EnumMeta):
    """This is enough to use ABC in Enum
    Usage:
    class MyABCEnum(Enum, metaclass=AbstractEnum):
    """


class ModelFamily(Enum, metaclass=AbstractEnum):
    """Define general properties for models of all companies"""

    @property
    def unique(self) -> str:
        """Unique bidirectional identifier for single model"""
        return f"{self.unique_letter}-{self.value}"

    @property
    def id_cli(self) -> str:
        """Colorized for Console output"""
        return f"{c.yellow(self.unique)}-{self.cli}"

    @property
    def cli(self) -> str:
        """Colorized for Console output"""
        return f"{self.family}.{c.magenta(self.name)}"

    @property
    def family(self) -> str:
        """Full name that is used for API call"""
        return self.__class__.__name__

    @property
    @abstractmethod
    def api_name(self) -> str:
        """Full name that is used for API call"""

    @property
    @abstractmethod
    def unique_letter(self) -> str:
        """Unique bidirectional identifier for model company"""

    @property
    @abstractmethod
    def target(self) -> str:
        """Identifier for FileUploader"""
