from __future__ import annotations

import logging
import time

from app.misc.jthread import JThread
from app.pipelines.pipeline import Pipeline


def external_task_to_process() -> None:
    time.sleep(1)
    print("External task processed")


class PipelineExample(Pipeline):
    def __init__(self, pipeline_tag: str, user_data: str) -> None:
        super().__init__(pipeline_tag)
        self._custom_user_data = user_data

    def on_pipeline_begin(self) -> None:
        super().on_pipeline_begin()
        self._custom_user_data += " P"

    def main(self, *args, **kwargs):
        time.sleep(0.2)
        self._custom_user_data = self.custom_task("I")
        time.sleep(0.2)
        self._custom_user_data = self.custom_task("P")

        workers = [
            JThread(target=self.heavy_processing, daemon=True, b_auto_start=True),
            JThread(target=external_task_to_process, daemon=True, b_auto_start=True),
        ]

        for _ in range(3):
            workers.append(JThread(target=self.async_custom_task, daemon=True, b_auto_start=True))

        for worker in workers:
            worker.join()

        for letter in "LINE":
            self._custom_user_data = self.custom_task(letter)

        return self._custom_user_data

    def custom_task(self, appendix: str) -> str:
        return f"{self._custom_user_data}-{appendix}"

    def async_custom_task(self) -> None:
        time.sleep(0.1)
        self._pipeline_logger.log(logging.INFO, "Async custom task has been processed!")

    def heavy_processing(self) -> None:
        time.sleep(0.5)
        self._pipeline_logger.log(logging.INFO, "Heavy processing is done!")


if __name__ == "__main__":
    pipeline_example = PipelineExample("pipeline_example", "Custom user data is:")
    processed_data = pipeline_example.run()
    print(processed_data)
