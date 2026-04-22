from pydantic import Field
from silvasta.config import SstSettings

from .defaults import Defaults
from .names import Names


class Settings(SstSettings):
    names: Names = Field(default_factory=Names)
    defaults: Defaults = Field(default_factory=Defaults)
