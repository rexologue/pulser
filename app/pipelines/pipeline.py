from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from app.misc.jthread import JThread
from app.misc.log_helper import LogHelper
from app.misc.scheduler import Scheduler


class Pipeline:
    """Base class for defining synchronous or asynchronous pipelines."""

    def __init__(self, pipeline_tag: str = "pipeline_0") -> None:
        self.start_time = datetime.now()
        self._on_finished_callable: Optional[Callable[[], None]] = None
        self._pipeline_tag = pipeline_tag
        self._pipeline_logger = LogHelper(pipeline_tag, "Pipeline Thread")
        self._pipeline_scheduler = Scheduler()
        self._b_done = False
        self._result: Any = None
        self._pipeline_thread: Optional[JThread] = None
        self._b_run_async = False

    def on_pipeline_begin(self) -> None:
        self.start_time = datetime.now()
        start_time_str = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        self._pipeline_logger.log(logging.INFO, "Enter pipeline %s, tag: %s", start_time_str, self._pipeline_tag)

    def on_pipeline_end(self) -> None:
        end_time = datetime.now()
        elapsed_time = end_time - self.start_time
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
        elapsed_time_str = str(elapsed_time)
        self._pipeline_logger.log(
            logging.INFO,
            "Finished pipeline %s, duration: %s, tag: %s",
            end_time_str,
            elapsed_time_str,
            self._pipeline_tag,
        )

        if self._on_finished_callable:
            self._on_finished_callable()
        self._b_done = True

    def main(self, *args, **kwargs):
        self._pipeline_logger.raise_exception_with_log(
            NotImplementedError("This pipeline does not implement main method and thus is invalid!"),
        )
        return None

    async def main_async(self, *args, **kwargs):
        self._pipeline_logger.raise_exception_with_log(
            NotImplementedError("This pipeline does not implement main method and thus is invalid!"),
        )
        return None

    def bind_on_pipeline_finished(self, on_finished: Callable[[], None]) -> None:
        self._on_finished_callable = on_finished

    def run(self, parallel: bool = False, *args, **kwargs):
        self._b_run_async = False
        if not parallel:
            return self._execute_run(*args, **kwargs)

        self._pipeline_thread = JThread(target=self._execute_run, args=args, kwargs=kwargs, daemon=True)
        self._pipeline_thread.start()
        self._pipeline_logger.log(
            logging.INFO,
            "Pipeline started in a parallel mode. The result of the work can be got from get_result().",
        )
        return None

    async def run_async(self, *args, **kwargs):
        self._b_run_async = True
        return await self._execute_run_async(*args, **kwargs)

    def _execute_run(self, *args, **kwargs):
        self.on_pipeline_begin()
        try:
            self._result = self.main(*args, **kwargs)
        finally:
            self.on_pipeline_end()
        return self._result

    async def _execute_run_async(self, *args, **kwargs):
        self.on_pipeline_begin()
        try:
            self._result = await self.main_async(*args, **kwargs)
        finally:
            self.on_pipeline_end()
        return self._result

    def wait_for(self) -> None:
        if self._b_run_async:
            self._pipeline_logger.raise_exception_with_log(ValueError("Cannot wait for an async pipeline!"))

        if self._pipeline_thread:
            self._pipeline_logger.log(logging.INFO, "Waiting for this pipeline to finish...")
            self._pipeline_thread.join()

    def get_result(self):
        if self._b_run_async:
            self._pipeline_logger.raise_exception_with_log(ValueError("Cannot get the result of an async pipeline!"))

        if self._pipeline_thread and self._pipeline_thread.is_alive():
            self.wait_for()

        return self._result

    def is_finished(self) -> bool:
        return self._b_done


class DynamicPipeline(Pipeline):
    _allow_instansiation = False
    _SYNC_TASK_TYPE = "sync"
    _PARALLEL_TASK_TYPE = "parallel"

    def __init__(self, pipeline_tag: str = "dynamic_pipeline_0") -> None:
        super().__init__(pipeline_tag)
        if DynamicPipeline._allow_instansiation:
            self.tasks: Dict[str, tuple[str, Callable[..., Any]]] = {}
            self._threads_pool: list[JThread] = []
        else:
            self._pipeline_logger.raise_exception_with_log(
                ValueError(
                    "This class can't be instantiated directly! Set DynamicPipeline._allow_instansiation = True "
                    "before constructing the instance."
                )
            )

    @classmethod
    def create_pipeline(cls, pipeline_tag: str, setup_function: Callable[["DynamicPipeline"], None]):
        cls._allow_instansiation = True
        instance = cls(pipeline_tag)
        cls._allow_instansiation = False

        setup_function(instance)
        return instance

    def main(self, *args, **kwargs):
        for task_type, task_callable in self.tasks.values():
            if task_type == DynamicPipeline._SYNC_TASK_TYPE:
                task_callable(*args, **kwargs)
            elif task_type == DynamicPipeline._PARALLEL_TASK_TYPE:
                thread = JThread(target=task_callable, args=args, kwargs=kwargs, daemon=True, b_auto_start=True)
                self._threads_pool.append(thread)
            else:
                self._pipeline_logger.raise_exception_with_log(
                    ValueError("Undefined task type! Tasks can be only 'sync' or 'parallel'"),
                )
        for thread in self._threads_pool:
            thread.join()
        self._threads_pool.clear()

    def task(self, tag: str, callable_task: Callable[..., Any]):
        self._add_task_internal(tag, callable_task, DynamicPipeline._SYNC_TASK_TYPE)

    def parallel_task(self, tag: str, callable_task: Callable[..., Any]):
        self._add_task_internal(tag, callable_task, DynamicPipeline._PARALLEL_TASK_TYPE)

    def wait(self, delay: float) -> None:
        def wait_task():
            time.sleep(delay)

        self.task("internal_wait_task", wait_task)

    def wait_all_parallels(self) -> None:
        def execute():
            for thread in self._threads_pool:
                thread.join()
            self._threads_pool.clear()

        self.task("internal_wait_all_parallels", execute)

    def _add_task_internal(self, tag: str, callable_task: Callable[..., Any], execution_type: str) -> None:
        task_key = tag if tag else callable_task.__name__
        self.tasks[task_key] = (execution_type, callable_task)


if __name__ == "__main__":
    def heavy_test_func():
        time.sleep(5)
        print("Heavy test func is done!")

    def setup_dynamic_pipeline(pipeline_ref: DynamicPipeline):
        pipeline_ref.task("Init", lambda: print("First task is executed!"))
        pipeline_ref.wait(2)
        pipeline_ref.parallel_task("Heavy task 1", heavy_test_func)
        pipeline_ref.parallel_task("Heavy task 2", heavy_test_func)
        pipeline_ref.wait(2)
        pipeline_ref.wait_all_parallels()
        pipeline_ref.task("End", lambda: print("All done!"))

    dynamic_pipeline = DynamicPipeline.create_pipeline("test_dynamic", setup_dynamic_pipeline)
    dynamic_pipeline.run()
    dynamic_pipeline.wait_for()
