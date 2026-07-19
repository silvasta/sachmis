import random
from dataclasses import dataclass, field

import fire
from sstcore import printer
from sstcore.exceptions import SstError
from sstcore.utils.exceptor import (
    ErrorList,
    Exceptor,
    ExceptorTask,
    ExceptorTaskHandler,
)

# NOTE: from dependencies, no issue to move to sachmis.exceptions (so far)
from sachmis.cli import app  # NOTE: as soon as this here is handled...
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


# IDEA: from here to modul sachmis.{utils|exceptions}.some_file_tbd.py

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
# NOTE: task and launch together? fits from the the target location and numbers

all_exceptions: list[SachmisLaunchError] = [all_data, all_task, all_lauch]

# NOTE: up to here all in a bundled module, probably together with SachmisExceptionHandler


@dataclass
class SachmisExceptionHandler(ExceptorTaskHandler):
    # NOTE: move maybe inside src somewhen? where?
    # utils or exceptions? synchronize with sstcore
    """Collect and Provide ExceptorTask Setup"""

    # AI: check the container
    # - suggest location inside project
    # - implement useful properties

    registry: list[ExceptorTask] = field(default_factory=list)

    # TASK: link args/kwargs IO (partial) here:
    # TODO: forward args for mock pipeline and to develop viz and log further
    # TODO: backward collect as like an observatory for (maybe after) runtime evaluation
    # TODO: export exceptions to project locations and cli.handlers

    # TODO: filter: grab by isinstance and provide by property
    # - maybe by comrehensions or by a simple dict[type[ SstError ]:SstError]

    @property
    def sachmis(self):
        return SachmisError

    @property
    def ancestor(self):
        return SstError

    @property
    def sachmis_exceptions(self) -> ErrorList:
        return [  # AI: somethins like this for any useful subcategory
            task.error
            for task in self.registry
            if isinstance(task.error, type[SachmisError])
        ]

    def random_exceptions(self, subset_size: int = 5) -> ErrorList:
        # AI: somethins like this but more useful
        return random.sample(self.sachmis_exceptions, subset_size)

    @property
    def roots(self):  # TODO: data,launch,task root
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


# INFO: below is the filled container that provides:
# - all exceptions
# - filtering for exceptions
# - later: connect with TUI and list selector
# - soon: assign example args here for mock pipeline
# - sooner: finish exceptions and define args first

# IDEA: maybe small module with a few export functions, at least 1
# - include all exception lists above, maybe accessible as imported module
exception_tasks = ExceptorTaskHandler(all_exceptions)


# IMPORTANT: this with the final cli functions (for the sachmis/example folder),
# - must be at top of file, close or directly below main!
class Exceptionator:
    def list(self):
        Exceptor(exception_tasks)

    def app(self):
        Exceptor(exception_tasks, app)

    def slow(self):
        exceptor = Exceptor(exception_tasks.all_exceptions, app, direct=False)
        printer(exceptor)

        input("ENTER")
        exceptor()

    def exception(self, num: int = 6):
        """Show __rich | str | repr__ of Exceptions"""
        for task in exception_tasks.random_exceptions(subset_size=num):
            exception = task.error
            # TEST:
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
            # TEST:
            printer.line()
            printer.box_bottom("the new bottom")
            printer(task)
            printer.box("the new box, now it starts")
            printer(task.load())
            printer.box_top("the new box with line at top")


if __name__ == "__main__":
    main()
