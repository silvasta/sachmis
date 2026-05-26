from contextlib import AbstractContextManager
from typing import Any

from loguru import logger
from tenacity import (
    Retrying,
    before_sleep_log,
    stop_after_attempt,
    wait_exponential,
)

from sachmis.config.defaults import TenacityDefaults

from ...config import SachmisConfig, get_config

config: SachmisConfig = get_config()


class FireRetry(AbstractContextManager):
    def __init__(self):
        logger.info("Setup Contex")

        self.td: TenacityDefaults = config.defaults.tenacity

        self.retryer = Retrying(
            stop=stop_after_attempt(self.td.max_attempts),
            wait=wait_exponential(**self.td.wait_exponential),
            before_sleep=before_sleep_log(logger, log_level=20),  # 20 = INFO
            reraise=True,
        )
        logger.debug("retryer setup finish")

    def __enter__(self):
        for attempt in self.retryer:
            logger.debug("start of next attempt")
            with attempt:
                if (current := attempt.retry_state.attempt_number) > 1:
                    logger.warning(f"Retry: {current}/{self.td.max_attempts}")
                else:
                    logger.debug("Executing initial API call...")
                yield

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        if exc_type is not None:
            logger.warning(f"Task failed with {exc_type.__name__}")
            return True

        logger.info("Got response, start processing...")

        return False


class Model:
    def fire(self):
        """Release prompt and process response with high-resilience retries."""
        logger.info("Fire")

        with FireRetry():
            self._raw_response: Any = self._get_response()

        self.process_response()

    def _get_response(self):
        pass

    def _handle_pipeline_failure(self, error: Exception):
        """Implement fallback logic for the DAG/Context here."""
        pass

    def process_response(self):
        pass
