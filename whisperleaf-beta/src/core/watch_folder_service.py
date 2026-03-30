"""Local-only watched folder: filesystem events via watchdog (optional dependency)."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:  # pragma: no cover
    FileSystemEventHandler = object  # type: ignore[misc, assignment]
    Observer = None  # type: ignore[misc, assignment]


class WatchFolderController:
    """Recursive directory observer; calls sync_file(root, abs_path) -> bool (did work)."""

    def __init__(
        self,
        *,
        sync_file: Callable[[Path, Path], bool],
        is_supported: Callable[[Path], bool],
    ) -> None:
        self._sync_file = sync_file
        self._is_supported = is_supported
        self._observer: Optional[Observer] = None
        self._root: Optional[Path] = None
        self._lock = threading.Lock()
        self._pending_feedback: Optional[str] = None

    def set_feedback(self, msg: str) -> None:
        with self._lock:
            self._pending_feedback = msg

    def peek_feedback(self) -> Optional[str]:
        with self._lock:
            return self._pending_feedback

    def take_feedback(self) -> Optional[str]:
        with self._lock:
            m = self._pending_feedback
            self._pending_feedback = None
            return m

    def snapshot(self) -> Dict[str, object]:
        with self._lock:
            active = self._observer is not None and self._root is not None
            path = str(self._root) if self._root else ""
        return {"watching": bool(active), "path": path}

    def stop(self) -> None:
        with self._lock:
            obs = self._observer
            self._observer = None
            self._root = None
        if obs:
            try:
                obs.stop()
                obs.join(timeout=8.0)
            except Exception:
                pass

    def start(self, root: Path) -> Tuple[bool, str]:
        self.stop()
        root = root.expanduser().resolve()
        if not root.is_dir():
            return False, "Folder not found"
        if Observer is None:
            return False, "File watching is unavailable (install the watchdog package)."

        debounce_lock = threading.Lock()
        last_fire: Dict[str, float] = {}

        controller = self

        def dispatch(abs_path: Path, notify: bool) -> None:
            with controller._lock:
                cur_root = controller._root
            if cur_root is None:
                return
            if not abs_path.is_file():
                return
            try:
                abs_resolved = abs_path.resolve()
                abs_resolved.relative_to(cur_root)
            except (ValueError, OSError):
                return
            if not controller._is_supported(abs_resolved):
                return
            key = str(abs_resolved)
            now = time.monotonic()
            with debounce_lock:
                t0 = last_fire.get(key, 0.0)
                if now - t0 < 0.65:
                    return
                last_fire[key] = now
            try:
                did = controller._sync_file(cur_root, abs_resolved)
                if did and notify:
                    controller.set_feedback("Updated from folder")
            except Exception as e:  # pragma: no cover
                print("[watch-folder] sync error: %s" % e)

        class Handler(FileSystemEventHandler):
            def on_created(self, event):  # type: ignore[no-untyped-def]
                if getattr(event, "is_directory", False):
                    return
                dispatch(Path(str(event.src_path)), True)

            def on_modified(self, event):  # type: ignore[no-untyped-def]
                if getattr(event, "is_directory", False):
                    return
                dispatch(Path(str(event.src_path)), True)

        try:
            observer = Observer()
            observer.schedule(Handler(), str(root), recursive=True)
            observer.start()
        except Exception as e:
            return False, str(e)

        with self._lock:
            self._observer = observer
            self._root = root

        def initial_scan() -> None:
            try:
                for p in root.rglob("*"):
                    if p.is_file() and self._is_supported(p):
                        try:
                            dispatch(p.resolve(), False)
                        except Exception as ex:
                            print("[watch-folder] initial skip %s: %s" % (p, ex))
            except Exception as e:
                print("[watch-folder] initial scan: %s" % e)

        threading.Thread(target=initial_scan, daemon=True).start()
        return True, ""
