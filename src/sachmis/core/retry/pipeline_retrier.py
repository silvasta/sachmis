from collections.abc import Callable
from typing import Any

from loguru import logger
from tenacity import (
    Retrying,
    before_sleep_log,
    stop_after_attempt,
    wait_exponential,
)

from ...config import SachmisConfig, get_config

config: SachmisConfig = get_config()


class PipelineRetrier:
    """Dedicated executor to handle Tenacity retry logic outside of Model."""

    def __init__(self):
        logger.debug("Setting up PipelineRetrier")
        self.td = config.defaults.tenacity

        self.retryer = Retrying(
            stop=stop_after_attempt(self.td.max_attempts),
            wait=wait_exponential(**self.td.wait_exponential),
            before_sleep=before_sleep_log(logger, log_level=20),  # INFO
            reraise=True,
        )

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Executes the provided callable within the retry loop."""
        try:
            for attempt in self.retryer:
                with attempt:
                    current = attempt.retry_state.attempt_number
                    if current > 1:
                        logger.warning(
                            f"Retry: {current}/{self.td.max_attempts}"
                        )
                    else:
                        logger.debug("Executing initial API call...")

                    # Execute the actual model call here
                    return func(*args, **kwargs)

        except Exception as e:
            # Catch the final reraised exception to prevent the whole
            # application from crashing if a node completely fails.
            logger.error(
                f"Task failed permanently with {type(e).__name__}: {e}"
            )
            return None


class Model:
    def fire(self):
        """Release prompt and process response with high-resilience retries."""
        logger.info("Fire")

        # Extremely slim execution block
        retrier = PipelineRetrier()
        self._raw_response = retrier.execute(self._get_response)

        # DAG/Pipeline flow control
        if self._raw_response is not None:
            logger.info("Got response, start processing...")
            self.process_response()
        else:
            self._handle_pipeline_failure(
                error=Exception("Max retries exceeded")
            )

    def _get_response(self) -> Any:
        # Concrete models implement their client logic here
        pass

    def _handle_pipeline_failure(self, error: Exception):
        """Implement fallback logic for the DAG/Context here."""
        pass

    def process_response(self):
        pass
