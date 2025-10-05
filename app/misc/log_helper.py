from __future__ import annotations

import logging
import sys
from typing import Optional


class LogHelper:
    """Utility wrapper around :mod:`logging` that standardises logger setup.

    Each pipeline component creates its own :class:`LogHelper` instance. The helper
    ensures that loggers are configured only once and exposes convenience methods
    for emitting messages and raising exceptions with context.
    """

    def __init__(self, name: str, thread_name: Optional[str] = None) -> None:
        self._logger = logging.getLogger(name)
        self._thread_name = thread_name or name
        self._ensure_configured()

    def _ensure_configured(self) -> None:
        if self._logger.handlers:
            return

        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s (%(threadName)s): %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    def log(self, level: int, message: str, *args, **kwargs) -> None:
        self._logger.log(level, message, *args, **kwargs)

    def raise_exception_with_log(self, exc: Exception) -> None:
        """Log the exception and re-raise it.

        Parameters
        ----------
        exc:
            The exception instance that should be raised.
        """

        self._logger.exception("Unhandled error in %s", self._thread_name)
        raise exc


__all__ = ["LogHelper"]
