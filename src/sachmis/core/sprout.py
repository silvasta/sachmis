from pathlib import Path

from ..config import SachmisConfig, get_config
from ..config.models import ModelFamily
from ..data import DataManager
from ..data.conversation import (
    ConversationDAG,
    Prompt,
    Response,
)
from ..data.conversation.fusion import SproutPackage


class Sprout:
    """Runtime Container for 1 Model with DAG SubGraph"""

    def __init__(self, package: SproutPackage, data: DataManager):
        self.next_response_id: str = package.response_uuid
        self.dag: ConversationDAG = package.dag_from_response
        self.prompt: Prompt = package.prompt
        self.model: ModelFamily = package.model
        self.previous_remote_id: str | None = package.previous_remote_id
        self.previous_response_uuid: str | None = (
            package.previous_response_uuid
        )
        # self.package: SproutPackage = package
        self.data: DataManager = data

    def collect_raw_response(self, full_response: str):
        config: SachmisConfig = get_config()
        full_response_path: Path = config.paths.full_response(
            topic=self.prompt.topic, model=self.model.unique
        )
        self.data._add_temporary_full_response(
            text=full_response, path=full_response_path
        )

    def collect_response_data(
        self,
        content: str,
        remote_id: str,
        usage: dict,
    ):
        response = Response(  # Important! override unique_id
            unique_id=self.next_response_id,
            content=content,
            remote_id=remote_id,
            usage=usage,
            topic=self.prompt.topic,
            sprout_id=self.prompt.sprout_id,
            tree_id=self.prompt.tree_id,
            model=self.model.unique,
        )
        self.data.handler.handle_response(response)
