from pydantic import BaseModel, Field

from ..data.conversation import ConversationDAG, DataDAG, Prompt, Response


class Sprout(BaseModel):  # IMPORTANT: BaseModel?
    """Runtime Container for 1 DAG"""

    data_dag: DataDAG = Field(default_factory=DataDAG)

    @property
    def prompts(self) -> dict[str, Prompt]:
        return self.data_dag.prompts

    @property
    def responses(self) -> dict[str, Response]:
        return self.data_dag.responses

    @property
    def dag(self) -> ConversationDAG:
        return self.data_dag.dag
