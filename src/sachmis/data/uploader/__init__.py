from ..files import RemoteState
from .google import GoogleUploader
from .uploader import FileUploader
from .xai import XaiUploader

type RemoteUploader = XaiUploader | GoogleUploader

match_table: dict[str, type[FileUploader]] = {
    "xai": XaiUploader,
    "google": GoogleUploader,
}


def create_uploader(identifier: str | RemoteState) -> type[RemoteUploader]:

    if isinstance(identifier, str):
        target: str = identifier

    elif isinstance(identifier, type(RemoteState)):
        target: str = identifier.target

    else:
        raise ValueError(f"Invalid: {identifier=}, {type(identifier)=}")

    return match_table[target]()


__all__: list[str] = [
    "FileUploader",
    "XaiUploader",
    "GoogleUploader",
    "RemoteUploader",
]
