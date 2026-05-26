from rich.progress import Progress
from tenacity import RetryCallState

from ...config import SachmisConfig, get_config
from ...config.defaults import TenacityDefaults

config: SachmisConfig = get_config()


def create_rich_retry_decorator():
    td: TenacityDefaults = config.defaults.tenacity

    progress = Progress()
    task_id = None

    def before_sleep_callback(retry_state: RetryCallState):
        nonlocal task_id
        if task_id is None:
            task_id = progress.add_task(
                f"[cyan]Calling {retry_state.fn.__qualname__}...",
                total=td.max_attempts,
            )

        progress.update(
            task_id,
            completed=retry_state.attempt_number - 1,
            description=f"[yellow]Retrying... (attempt {retry_state.attempt_number})",
        )

    # ... return retry(...) with before_sleep=before_sleep_callback
