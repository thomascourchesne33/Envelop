import logging
import os
import threading
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

log = logging.getLogger("fcf")


class _XlsxHandler(FileSystemEventHandler):
    def __init__(self, xlsx_path: str, callback: Callable) -> None:
        self._path = os.path.abspath(xlsx_path)
        self._callback = callback
        self._timer: threading.Timer | None = None

    def _debounced_reload(self) -> None:
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(1.5, self._callback)
        self._timer.daemon = True
        self._timer.start()

    def on_modified(self, event):
        if not event.is_directory and os.path.abspath(event.src_path) == self._path:
            log.info("File changed, scheduling reload")
            self._debounced_reload()

    def on_created(self, event):
        self.on_modified(event)


class FileWatcher:
    def __init__(self) -> None:
        self._observer: Observer | None = None
        self._handler: _XlsxHandler | None = None

    def start(self, xlsx_path: str, callback: Callable) -> None:
        self.stop()
        watch_dir = os.path.dirname(os.path.abspath(xlsx_path))
        self._handler = _XlsxHandler(xlsx_path, callback)
        self._observer = Observer()
        self._observer.schedule(self._handler, watch_dir, recursive=False)
        self._observer.daemon = True
        self._observer.start()
        log.info("Watching %s", watch_dir)

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None
