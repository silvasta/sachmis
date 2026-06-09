from typing import Self

from ..data import DataManager
from ..data.conversation import ConversationDAG, DataDAG, Prompt, Response


class Sprout:  # IMPORTANT: BaseModel?
    """Runtime Container for 1 DAG"""

    def __init__(
        self,
        data_dag: DataDAG,
        data: DataManager,
    ):

        self.data_dag: DataDAG = data_dag
        self.data: DataManager = data

    # NEXT:
    # - previous_response_id
    # - images from prompt
    # - files
    @classmethod  # TASK: this or init?
    def setup(cls, *args, **kwargs) -> Self:
        # return cls()
        raise NotImplementedError

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

    @property
    def active_prompt(self) -> Prompt:
        raise NotImplementedError

    @property
    def prompts(self) -> dict[str, Prompt]:
        return self.data_dag.prompts

    @property
    def responses(self) -> dict[str, Response]:
        return self.data_dag.responses

    @property
    def dag(self) -> ConversationDAG:
        return self.data_dag.dag
