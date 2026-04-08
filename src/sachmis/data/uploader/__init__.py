from .google import GoogleUploader
from .uploader import FileUploader
from .xai import XaiUploader

all = [
    GoogleUploader,
    XaiUploader,
    FileUploader,
]
