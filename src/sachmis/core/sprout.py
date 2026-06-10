from typing import Self

from ..data import DataManager
from ..data.conversation import ConversationDAG, Prompt, Response
from ..data.conversation.fusion import SproutPackage


class Sprout:
    """Runtime Container for 1 Model with DAG SubGraph"""

    def __init__(self, package: SproutPackage, data: DataManager):
        self.next_response_id: str = package.response_uuid

        self.dag: ConversationDAG = package.dag_from_response
        self.prompt: Prompt = package.prompt

        self.has_previous_response: bool = (
            package.previous_remote_id is not None
        )
        self.package: SproutPackage = package
        self.data: DataManager = data

    @property
    def response_node(self):
        """Provide active Response Node"""

    def check_ancestor(self) -> bool:
        # NEXT: Forward DataManager
        # NEXT: Forward DataManager
        # NEXT: Forward DataManager
        # NEXT: Forward DataManager
        # NEXT: Forward DataManager

        self.active_node
        uid: str | None = self.data.handler.provide_grandfather_uuid()
        if uid is None:
            return False
        return True

    def collect_raw_response(self, full_response: str):
        # NEXT: Forward DataManager
        # full_response_path: Path = config.paths.full_response(
        #     topic=self.sprout.topic, model=self.model.unique)
        # self.data._add_temporary_full_response(
        #     text=full_response, path=full_response_path)
        raise NotImplementedError

    def collect_response_data_from_chat(
        self, content: str, remote_id: str, usage: dict
    ):
        # NEXT: define data packages
        # content=content,
        # remote_id=response_id,
        # usage=usage,
        # NEXT: Forward handler
        raise NotImplementedError
