from __future__ import annotations

import threading
from typing import Callable, Optional


class ScheduledTask:
    def __init__(self, interval: float, func: Callable, *, repeat: bool = True) -> None:
        self.interval = interval
        self.func = func
        self.repeat = repeat
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
        self._cancelled = False

    def _run(self) -> None:
        with self._lock:
            if self._cancelled:
                return
        self.func()
        if self.repeat:
            self.start()

    def start(self) -> None:
        with self._lock:
            if self._cancelled:
                return
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.daemon = True
            self._timer.start()

    def cancel(self) -> None:
        with self._lock:
            self._cancelled = True
            if self._timer:
                self._timer.cancel()


class Scheduler:
    """Extremely small scheduler used by the pipeline infrastructure."""

    def __init__(self) -> None:
        self._tasks: list[ScheduledTask] = []

    def schedule(self, interval: float, func: Callable, *, repeat: bool = True) -> ScheduledTask:
        task = ScheduledTask(interval, func, repeat=repeat)
        self._tasks.append(task)
        task.start()
        return task

    def cancel_all(self) -> None:
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()

    def __enter__(self) -> "Scheduler":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.cancel_all()


__all__ = ["Scheduler", "ScheduledTask"]
