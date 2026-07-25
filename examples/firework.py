import random
from dataclasses import dataclass, field
from pathlib import Path

import fire
from sstcore import printer
from sstcore.exceptions import SstError
from sstcore.utils.exceptor import (
    ErrorList,
    Exceptor,
    ExceptorTask,
    ExceptorTaskHandler,
)

from sachmis.exceptions import (
    ApiCallError,
    ArborealDataError,
    ArborealError,
    ArborealTrackingError,
    CapstoneError,
    ConversationError,
    DataInputOutputError,
    DataOperationError,
    DataRuntimeError,
    DummiError,
    GeminiError,
    GrokError,
    NotInCampError,
    PromptError,
    ResponseError,
    SachmisDataError,
    SachmisError,
    SachmisLaunchError,
    SachmisTaskError,
    SproutError,
    TreeGraphError,
)


def main():
    fire.Fire(Exceptionator)


class Exceptionator:
    def arbo(self):
        Exceptor(arbo_loaded)

    def list(self):
        Exceptor(exception_tasks)

    def app(self):
        from sachmis.cli import app

        Exceptor(exception_tasks, app)

    def slow(self):
        from sachmis.cli import app

        exceptor = Exceptor(exception_tasks.all_exceptions, app, direct=False)
        printer(exceptor)

        input("ENTER")
        exceptor()

    def exception(self, num: int = 6):
        """Show __rich | str | repr__ of Exceptions"""
        for task in exception_tasks.random_exceptions(subset_size=num):
            exception = task.error
            printer.header(f"Launch from CLI: {str} = {exception}")
            printer.header(f"Launch from CLI: {type(str)} = {exception}")
            printer.header(f"Launch from CLI: = {exception._name}")
            printer(exception)
            printer(f"state of {exception._name} at crash: {exception=}")

    def error(self):
        """Load Exceptions and boom..."""
        tasks: list[ExceptorTask] = ExceptorTask.ensure(
            [exception_tasks.ancestor, exception_tasks.sachmis]
        )  # just as first example

        for task in tasks:
            printer.line()
            printer.box_bottom("the new bottom")
            printer(task)
            printer.box("the new box, now it starts")
            printer(task.load())
            printer.box_top("the new box with line at top")


root: list[Exception] = [
    SstError,
]
project_root: list[SstError] = [
    SachmisError,
]
# - Data
data_root: list[SachmisError] = [
    SachmisDataError,
]
data_operation: list[SachmisDataError] = [
    DataOperationError,
    #
    DataRuntimeError,
    DataInputOutputError,
]
data_conversation: list[SachmisDataError] = [
    ConversationError,
    #
    PromptError,
    ResponseError,
    TreeGraphError,
]
data_arboreal: list[SachmisDataError] = [
    ArborealError,
    #
    ArborealDataError,
    ArborealTrackingError,
]
# - Task
task_exceptions: list[SachmisError] = [
    SachmisTaskError,
]
task_exceptions: list[SachmisTaskError] = [
    CapstoneError,
    SproutError,
    ApiCallError,
]
model_exceptions: list[ApiCallError] = [
    GeminiError,
    GrokError,
    DummiError,
]
# - Launch
launch_root: list[SachmisError] = [
    SachmisLaunchError,
]
launch_exception: list[SachmisLaunchError] = [
    NotInCampError,
]

all_data: list[SachmisDataError] = [launch_root, launch_exception]
all_task: list[SachmisTaskError] = [launch_root, launch_exception]
all_lauch: list[SachmisLaunchError] = [launch_root, launch_exception]

all_exceptions: list[SachmisLaunchError] = [all_data, all_task, all_lauch]


### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --
### Loaded
### -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- -- - -- -- --

arbo_loaded: list[ExceptorTask] = [
    ExceptorTask(error=ArborealError),
    ExceptorTask(error=ArborealDataError, args=("Duplicate",), kwargs={}),
    ExceptorTask(
        error=ArborealTrackingError,
        args=(Path(".t_101_test.json"),),
        kwargs={"issue": "Missing", "arbo": "Tree"},
    ),
]


@dataclass
class SachmisExceptionHandler(ExceptorTaskHandler):
    # NOTE: move maybe inside src somewhen? where?
    # utils or exceptions? synchronize with sstcore
    """Collect and Provide ExceptorTask Setup"""

    registry: list[ExceptorTask] = field(default_factory=list)

    @property
    def sachmis(self):
        return SachmisError

    @property
    def ancestor(self):
        return SstError

    @property
    def sachmis_exceptions(self) -> ErrorList:
        return [
            task.error
            for task in self.registry
            if isinstance(task.error, type[SachmisError])
        ]

    def random_exceptions(self, subset_size: int = 5) -> ErrorList:
        return random.sample(self.sachmis_exceptions, subset_size)

    @property
    def roots(self):
        raise NotImplementedError

    # TODO: data_exc...
    #
    # TODO: launch_exc...

    # TODO: task..

    # INFO: the following 2 classmethods +1 property exist in: ExceptorTaskHandler
    # @classmethod
    # def arise(cls, tasks: ErrorList) -> Self:...
    #     """Arise from the confirmed List of given Task and Exceptions"""
    # @classmethod
    # def ensure(cls, tasks: ErrorList) -> list[ExceptorTask]:...
    #     """Confirm List and provide valid ExceptorTasks"""
    # @property
    # def all_exceptions(self) -> ErrorList:...


exception_tasks = ExceptorTaskHandler(all_exceptions)


if __name__ == "__main__":
    main()
