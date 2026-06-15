from typing import Any

from loguru import logger
from tenacity import (
    Retrying,
    before_sleep_log,
    stop_after_attempt,
    wait_exponential,
)

# ... (imports) ...


class Model(ABC):
    # ... (init and other methods) ...

    def fire(self):
        """Release prompt and process response with high-resilience retries."""
        logger.info("Fire")

        td = config.defaults.tenacity

        retryer = Retrying(
            stop=stop_after_attempt(td.max_attempts),
            wait=wait_exponential(**td.wait_exponential),
            before_sleep=before_sleep_log(logger, log_level=20),  # 20 = INFO
            reraise=True,
        )

        try:
            for attempt in retryer:
                with attempt:
                    # Look at this! Tenacity tracks the count for you.
                    current_try = attempt.retry_state.attempt_number
                    if current_try > 1:
                        logger.warning(
                            f"Retry attempt {current_try}/{td.max_attempts}"
                        )
                    else:
                        logger.debug("Executing initial API call...")

                    self._raw_response: Any = self._get_response()

        except Exception as e:
            # PIPELINE PROTECTION:
            # If reraise=True, the final exception bubbles up here after all retries fail.
            # In a DAG/Pipeline, you might want to catch this, log it, and
            # write a "FAILED" state to your Context rather than crashing the app.
            logger.error(
                f"Execution completely failed after {td.max_attempts} attempts: {e}"
            )
            self._handle_pipeline_failure(e)
            return  # Exit cleanly

        logger.info("Got response, start processing...")
        self.process_response()

    @abstractmethod
    def _get_response(self):
        pass

    def _handle_pipeline_failure(self, error: Exception):
        """Implement fallback logic for the DAG/Context here."""
        pass
