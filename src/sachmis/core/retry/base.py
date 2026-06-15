from loguru import logger
from tenacity import (
    RetryCallState,
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ...config import get_config


def base_model():
    """Main retry decorator factory for Model calls"""
    config = get_config()
    td = config.defaults.tenacity

    def before_sleep_callback(retry_state: RetryCallState):
        logger.opt(colors=True).warning(
            f"<yellow>Attempt {retry_state.attempt_number}/{td.max_attempts} failed "
            f"for {retry_state.fn.__qualname__}. "
            f"Waiting {retry_state.next_action.sleep:.1f}s...</yellow>"
        )

    return retry(
        stop=stop_after_attempt(td.max_attempts),
        wait=wait_exponential(**td.wait_exponential),
        before_sleep=before_sleep_callback,
        after=after_log(logger, log_level=20),
        retry=retry_if_exception_type(
            (
                TimeoutError,
                ConnectionError,
                # Add your custom exceptions here
            )
        ),
        reraise=True,
    )


# Optional: more specialized versions
def rich_style():
    return base_model()


def relaxed():
    return base_model()


def push_forward():
    return base_model()
