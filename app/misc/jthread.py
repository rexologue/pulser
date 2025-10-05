from __future__ import annotations

import threading
from typing import Any, Callable, Iterable, Optional


class JThread(threading.Thread):
    """A small convenience wrapper around :class:`threading.Thread`.

    The original codebase relied on a custom *joinable thread* abstraction. This
    class keeps the behaviour but provides a safer constructor and an optional
    auto-start flag.
    """

    def __init__(
        self,
        *,
        target: Optional[Callable[..., Any]] = None,
        args: Iterable[Any] | None = None,
        kwargs: Optional[dict[str, Any]] = None,
        daemon: bool | None = None,
        b_auto_start: bool = False,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(
            target=target,
            args=tuple(args or ()),
            kwargs=kwargs or {},
            daemon=daemon,
            name=name,
        )
        if b_auto_start:
            self.start()


__all__ = ["JThread"]
