from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Self

from loguru import logger
from pydantic import Field, model_validator

from sachmis.config import SachmisConfig, get_config
from sachmis.utils.exceptions import SproutResponseExistsError

from ..files import Prompt, Response
from .base import Arboreal


class Sprout(Arboreal):
    """Successor of Tree, can have own successors"""

    model: str
    prompt: Prompt
    response: Response | None

    sprout_locator: Path  # NOTE: some id/path hack
    sprouts: list[Self] = Field(default_factory=list)

    # LATER: group that with Status(Enum) or similar
    extracted_at: datetime | None = None
    loaded_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Arboreal - Access to Members
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    @property
    def n_children(self) -> int:
        return len(self.sprouts)

    @property
    def count_all_sprouts(self) -> int:
        """Including Sprout that is called down to any leaf"""
        return 1 + sum(sprout.count_all_sprouts for sprout in self.sprouts)

    def _next_sprout_locator(self) -> Path:
        next_locator: Path = self.sprout_locator / f"{self._next_instance_id}"
        logger.debug(f"sprout {self.unique_id} created {next_locator=}")
        return next_locator

    def attach_sprout_to_sprout(self, model, prompt) -> Self:
        new_sprout: Self = self.__class__(
            model=model,
            prompt=prompt,
            response=None,
            sprout_locator=self._next_sprout_locator(),
        )
        return self._attach(new_sprout)

    def _attach(self, sprout: Self) -> Self:
        self.sprouts.append(sprout)
        logger.debug(f"Attached Sprout {sprout.sprout_locator} to Sprout")
        return sprout

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Sprout - Health checks, maybe -> ArborealDisk?
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    # LATER: Enum status:
    # - created, init status
    # - extracted (tree loaded, sprout attached, sprout attached to task, tree closed, ...)
    #   - cant be extracted again by other task, other task still can extract new created sprouts at same knot
    # - loaded, prompt loaded from Model to chat, waiting for launch
    #   - above/below probably redundant, still curious about differences, especially for multi pipelines
    # - started, launched in pipeline, connected or not with tree
    # - completed, response received and attached, ready for new sprouts
    #   - can be reattached to tree
    # failed states: maybe grouped as 1
    #   - could be reattached to tree, maybe for completeness, or deleted there
    # - crashed, known failure
    # - lost, unknown failure

    @model_validator(mode="after")
    def enforce_consistency(self) -> "Sprout":
        """Check if crashed during runtime or API call"""

        if self.response is not None and self.completed_at is None:
            msg = "Repairing damaged Sprout, has Response but missing date: completed_at"
            logger.warning(msg)
            self.completed_at: datetime = datetime.now(UTC)

        return self

    @property
    def has_started(self) -> bool:
        """Returns started_at avaliable but not Response avaliable"""
        return self.started_at is not None and self.completed_at is None

    @property
    def has_finished(self) -> bool:
        """Check if Response and completed_at date avaliable"""
        return self.completed_at is not None and self.response is not None

    @property
    def is_failed(self) -> bool:
        """Derive the failed state dynamically."""
        if self.has_started:
            thresh = timedelta(hours=1)  # PARAM:
            if (running_for := datetime.now() - self.started_at) > thresh:  # ty:ignore
                logger.debug(f"sprout failed, {running_for=}, {thresh=}")
                return True
        return False

    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###
    ### -- Sprout - Custom Functions and Atributes
    ### -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- -- - -- ###

    def set_extracted(self):
        self.extracted_at: datetime = self.touch()

    def set_loaded(self):
        self.loaded_at: datetime = self.touch()

    def set_started(self):
        self.started_at: datetime = self.touch()

    def set_completed(self):
        self.completed_at: datetime = self.touch()

    def attach_response(self, response: Response, exists_ok=False):
        if self.response is None:
            logger.debug("Attached Response to Sprout")
        elif exists_ok:
            logger.warning("Override Response in Sprout")
        else:
            raise SproutResponseExistsError(self.unique_id)
        self.response: Response = response
        self.set_completed()

    @property
    def answer_path(self) -> Path:
        """Calculated from CWD, used to save response"""
        config: SachmisConfig = get_config()
        return config.paths.answer_file(
            self.prompt.topic,
            locator=f"{self.sprout_locator}",
            model=self.model,
        )

    @property
    def write_answer_get_path(self) -> Path:
        if self.response is None:
            raise AttributeError(f"Can't process empty response of {self=}")
        unique_answer_path: Path = self.answer_path
        unique_answer_path.write_text(self.response.content)
        return unique_answer_path
