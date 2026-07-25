from enum import Enum, auto

from rich.console import RenderableType
from sstcore.contract.cli import PanelDTO
from sstcore.contract.external import RichProtocol
from sstcore.contract.log import LogDTO
from sstcore.exceptions import NotImplementedDispatchError
from sstcore.utils import ColorBox

c = ColorBox()


class Status(Enum):  # TODO: rename if actally used
    # AI: unsure if for Files, States, Uploader or all
    CONFIRMED = auto()
    FETCHED = auto()
    CONFLICT = auto()
    INIT = auto()

    @property
    def color(self) -> str:  # LATER: return color from palette
        match self:
            case self.CONFIRMED:
                return "green"
            case self.FETCHED:
                return "orange3"
            case self.CONFLICT:
                return "red"
            case self.INIT:
                return "cyan"

    @classmethod
    def from_bool(cls, x: bool, y: bool) -> Status:
        # AI: somehow not comletele thought through...
        match (x, y):
            case (True, True):
                return cls.CONFIRMED
            case (True, False):
                return cls.FETCHED
            case (False, False):
                return cls.CONFLICT
            case (False, True):
                return cls.INIT
            case _:
                raise NotImplementedDispatchError((x, y), Status, "why?")


class SimpleNameMixin:  # TODO: synchronize with rich, use StyledName
    def __str__(self) -> str:
        return type(self).__name__


class RichAmpel:
    status: Status = Status.INIT

    def __rich__(self) -> str:
        return c(self, self.status.color)


class UploadViews:
    remote_files = []

    def __cli__(self):
        title: RenderableType = (
            self.__rich__() if isinstance(self, RichProtocol) else str(self)
        )
        PanelDTO.from_call(
            target=self.remote_files,
            title=title,
        )

    def __log__(self):
        return LogDTO(
            message=f"{self}[{len(self.remote_files)}]",
            level="INFO",
            metrics={"files": self.remote_files},
        )

    def __repr__(self) -> str:
        return f"{self}[{self.remote_files}]"
