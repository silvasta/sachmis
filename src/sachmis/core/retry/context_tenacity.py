from abc import ABC
from contextlib import contextmanager

from loguru import logger
from tenacity import (
    RetryCallState,
    Retrying,
    stop_after_attempt,
    wait_exponential,
)

from ...config import get_config


@contextmanager
def fire_with_retry():
    """Context manager for retrying API calls in Model.fire()"""
    config = get_config()
    td = config.defaults.tenacity

    def before_sleep_callback(retry_state: RetryCallState):
        if retry_state.attempt_number > 1:
            logger.opt(colors=True).warning(
                f"<yellow>Retry {retry_state.attempt_number}/{td.max_attempts} "
                f"after failure. Waiting {retry_state.next_action.sleep:.1f}s...</yellow>"
            )

    retryer = Retrying(
        stop=stop_after_attempt(td.max_attempts),
        wait=wait_exponential(**td.wait_exponential),
        before_sleep=before_sleep_callback,
        reraise=True,
    )

    logger.info("Starting request with retry support...")

    for attempt in retryer:
        with attempt:
            if attempt.retry_state.attempt_number > 1:
                logger.warning(
                    f"Retrying attempt {attempt.retry_state.attempt_number}"
                )
            yield  # The code inside the `with` block runs here
            # If we reach here → success
            logger.success("Request succeeded")
            return


class Model(ABC):
    def fire(self):
        """Release prompt and process response with retries"""
        logger.info(f"🚀 Firing {self.model.api_name}...")

        with fire_with_retry():
            self._raw_response: Any = self._get_response()

        logger.info("Got response, start processing...")
        self.process_response()
