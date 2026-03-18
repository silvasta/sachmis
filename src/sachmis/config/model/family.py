from abc import ABCMeta, abstractmethod
from enum import Enum, EnumMeta

# INFO: this is a Model param schema for fixed external data

# REFACTOR: Use csv instead of Enum?
# - needs factory for Enum or Literal for typer


class AbstractEnum(ABCMeta, EnumMeta):
    """This is enough to use ABC in Enum
    Usage:
    class MyABCEnum(Enum, metaclass=AbstractEnum):
    """


class ModelFamily(Enum, metaclass=AbstractEnum):
    """Define general properties for models of all companies"""

    # TASK: load family from csv
    # - load including prices, status=Active etc,
    # check file-analyzer for template pydantic read/write

    @property
    def topicality(self) -> str:  # TODO: don't forget update!
        """Last update of price list, token names or new models"""
        # TASK: make this somehow better
        return "21.01.2026"

    @property
    def unique(self) -> str:
        """Unique bidirectional identifier for single model"""
        # LATER: bidirectional backwards transform
        # - how to handle category_unique? another Enum?
        return f"{self.category_unique}-{self.value}"

    @property
    @abstractmethod
    def api_name(self) -> str:
        """Full name that is used for API call"""
        raise NotImplementedError(f"Missing api_name for: {self}")

    @property
    @abstractmethod
    def category_unique(self) -> str:
        """Unique bidirectional identifier for model category (company)"""
        raise NotImplementedError(f"Missing category_unique for: {type[self]}")
