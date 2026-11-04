"""Gestor local de tareas en segundo plano (sin Celery ni Redis)."""

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable

log = logging.getLogger(__name__)


class ExtractionCancelled(Exception):
    """Se lanza dentro del worker cuando se solicitó la cancelación."""


class LocalTaskManager:
    def __init__(self, max_workers: int = 2) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="extraction")
        self._events: dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def submit(self, task_id: str, fn: Callable[[threading.Event], None]) -> None:
        event = threading.Event()
        with self._lock:
            self._events[task_id] = event
        future: Future = self._executor.submit(fn, event)
        future.add_done_callback(lambda _f: self._release(task_id))

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            event = self._events.get(task_id)
        if event is None:
            return False
        event.set()
        return True

    def _release(self, task_id: str) -> None:
        with self._lock:
            self._events.pop(task_id, None)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)