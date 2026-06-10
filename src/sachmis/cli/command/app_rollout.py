from ...config import SachmisConfig, get_config
from ...data.handler import FileRollout
from ...utils.print import printer

config: SachmisConfig = get_config()


def rollout(  # TASK: this as selector of current file tree!
):
    """Test File to Filesystem Mapping for write only files"""
    handler = FileRollout()
    printer(handler)
