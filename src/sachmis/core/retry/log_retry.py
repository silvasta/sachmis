from loguru import logger
from tenacity import (
    RetryCallState,
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from sachmis.config.defaults import TenacityDefaults

from ..config import SachmisConfig, get_config
from ..exceptions import SachmisDataError

config: SachmisConfig = get_config()


def create_model_retry_decorator():
    """Factory that returns a rich retry decorator"""
    td: TenacityDefaults = config.defaults.tenacity

    def before_sleep_callback(retry_state: RetryCallState):
        """Custom logging with attempt info"""
        logger.warning(
            f"Attempt {retry_state.attempt_number} failed for {retry_state.fn.__qualname__}. "
            f"Waiting {retry_state.next_action.sleep:.1f}s before retry. "
            f"Exception: {retry_state.outcome.exception()}"
        )

    return retry(
        stop=stop_after_attempt(td.max_attempts),
        wait=wait_exponential(**td.wait_exponential),
        # Logging
        before_sleep=before_sleep_callback,  # Custom rich log
        # before_sleep=before_sleep_log(logger, log_level=20),  # Simple version
        after=after_log(
            logger, log_level=20
        ),  # Log after successful retry too
        # Only retry on specific exceptions (highly recommended)
        retry=retry_if_exception_type(
            (
                TimeoutError,
                ConnectionError,
                SachmisDataError,  # your custom ones
                # Add API-specific rate limit errors etc.
            )
        ),
        reraise=True,
        # retry_error_callback=...   # final failure handler
    )


def before_sleep_callback(retry_state: RetryCallState):
    logger.opt(colors=True).info(
        f"<yellow>Attempt {retry_state.attempt_number}/{td.max_attempts} "
        f"failed. Next retry in {retry_state.next_action.sleep:.1f}s</yellow>"
    )
