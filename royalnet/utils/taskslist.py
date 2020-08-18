import asyncio as aio
import logging
from typing import *

from .sentry import sentry_exc

log = logging.getLogger(__name__)


class TaskList:
    def __init__(self, loop: aio.AbstractEventLoop):
        self.loop: aio.AbstractEventLoop = loop
        self.tasks: List[aio.Task] = []

    def collect(self):
        """Remove finished tasks from the list."""
        log.debug(f"Collecting done tasks")
        new_list = []
        for task in self.tasks:
            try:
                task.result()
            except aio.CancelledError:
                log.warning(f"Task {task} was unexpectedly cancelled.")
            except aio.InvalidStateError:
                log.debug(f"Task {task} hasn't finished running yet, readding it to the list.")
                new_list.append(task)
            except Exception as err:
                sentry_exc(err)
        self.tasks = new_list

    def add(self, coroutine: Awaitable[Any], timeout: float = None) -> aio.Task:
        """Add a new task to the list; the task will be cancelled if ``timeout`` seconds pass."""
        log.debug(f"Creating new task {coroutine}")
        if timeout:
            task = self.loop.create_task(aio.wait_for(coroutine, timeout=timeout))
        else:
            task = self.loop.create_task(coroutine)
        self.tasks.append(task)
        return task
