from abc import ABCMeta, abstractmethod
from enum import Enum, EnumMeta

from sstcore.utils.print import ColorBox

# INFO: this is the Model Param Schema for fixed external data

c = ColorBox()


class AbstractEnum(ABCMeta, EnumMeta):
    """This is enough to use ABC in Enum
    Usage:
    class MyABCEnum(Enum, metaclass=AbstractEnum):
    """


class ModelFamily(Enum, metaclass=AbstractEnum):
    """Define general properties for models of all companies"""

    # LATER: load family from csv
    # - load including prices, status=Active etc,
    # check file-analyzer for template pydantic read/write
    # REFACTOR: Use csv/pyandtic instead of Enum?
    # - still nice with Enum, match and validation
    # - maybe basemodel just for data?

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
