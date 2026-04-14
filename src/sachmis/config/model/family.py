from abc import ABCMeta, abstractmethod
from enum import Enum, EnumMeta

# INFO: this is the Model Param Schema for fixed external data

# REFACTOR: Use csv/pyandtic instead of Enum?
# - needs factory for Enum or Literal for typer XXX already changed!
# - still nice with Enum, match and validatoin
# - maybe basemodel just for usage?


class AbstractEnum(ABCMeta, EnumMeta):
    """This is enough to use ABC in Enum
    Usage:
    class MyABCEnum(Enum, metaclass=AbstractEnum):
    """


class ModelFamily(Enum, metaclass=AbstractEnum):
    """Define general properties for models of all companies"""

    # IMPORTANT: make 1 word target identifier, eiter as Company Enum or ...
    # TASK: load family from csv
    # - load including prices, status=Active etc,
    # check file-analyzer for template pydantic read/write

    @property
    def unique(self) -> str:
        """Unique bidirectional identifier for single model"""
        return f"{self.unique_letter}-{self.value}"

    @property
    @abstractmethod
    def api_name(self) -> str:
        """Full name that is used for API call"""

    @property
    @abstractmethod
    def unique_letter(self) -> str:
        """Unique bidirectional identifier for model company"""
