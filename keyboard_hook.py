import ctypes
import ctypes.wintypes
import logging
import threading
from typing import Callable

import keyboard

log = logging.getLogger("fcf")

# Allow-list: the "/" trigger only ever activates when Outlook is the foreground app.
# This also prevents the picker from reappearing while typing inside our own dialogs
# (variable popup, template editor) since those run under Envelop.exe, not OUTLOOK.EXE.
ALLOWED_PROCESSES = {"outlook.exe"}

DISMISS_KEYS = {
    "enter", "tab", "delete",
    "up", "down", "left", "right",
    "page up", "page down", "home", "end",
    "f1","f2","f3","f4","f5","f6","f7","f8","f9","f10","f11","f12",
}

MODIFIER_KEYS = {
    "shift", "left shift", "right shift",
    "ctrl", "left ctrl", "right ctrl",
    "alt", "left alt", "right alt",
    "caps lock", "num lock", "scroll lock",
    "left windows", "right windows",
}


def _get_foreground_process() -> str:
    """Return the lowercase exe name of the foreground window's process, or "" on failure.

    Uses QueryFullProcessImageNameW (needs only PROCESS_QUERY_LIMITED_INFORMATION) instead of
    GetModuleBaseNameW (needs PROCESS_VM_READ), which can silently fail for processes like
    OUTLOOK.EXE depending on privilege/architecture, breaking the foreground check.
    """
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        pid = ctypes.wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid.value)
        if not h:
            return ""
        buf = ctypes.create_unicode_buffer(260)
        size = ctypes.wintypes.DWORD(260)
        ok = ctypes.windll.kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size))
        ctypes.windll.kernel32.CloseHandle(h)
        if not ok:
            return ""
        path = buf.value
        return path.rsplit("\\", 1)[-1].lower()
    except Exception:
        return ""


class KeyboardHook:
    def __init__(
        self,
        get_trigger_char: Callable[[], str],
        get_templates: Callable,
        on_buffer_update: Callable[[str, list], None],
        on_clear: Callable[[], None],
    ) -> None:
        self._get_trigger = get_trigger_char
        self._get_templates = get_templates
        self._on_update = on_buffer_update
        self._on_clear = on_clear
        self._buffer = ""
        self._capturing = False
        self._paused = False
        # RLock: reentrant — same thread can acquire multiple times without deadlock
        self._lock = threading.RLock()
        self._hooked = False

    def start(self) -> None:
        if self._hooked:
            return
        keyboard.hook(self._on_key_event, suppress=False)
        self._hooked = True
        log.info("Keyboard hook started")

    def stop(self) -> None:
        if self._hooked:
            keyboard.unhook_all()
            self._hooked = False

    def pause(self) -> None:
        with self._lock:
            self._paused = True
            self._buffer = ""
            self._capturing = False

    def resume(self) -> None:
        with self._lock:
            self._paused = False

    def clear_buffer(self) -> None:
        with self._lock:
            self._buffer = ""
            self._capturing = False

    def _on_key_event(self, event) -> None:
        if event.event_type != keyboard.KEY_DOWN:
            return

        with self._lock:
            if self._paused:
                return

        try:
            proc = _get_foreground_process()
            # Fail open: if detection fails (empty result), don't block the trigger.
            if proc and proc not in ALLOWED_PROCESSES:
                return
        except Exception:
            pass

        action = None   # ("update", buffer, matches) | ("clear",)

        with self._lock:
            trigger = self._get_trigger()

            # "/" always (re)starts a fresh capture
            if event.name == trigger:
                self._buffer = trigger
                self._capturing = True
                from template_loader import filter_templates
                matches = filter_templates(self._get_templates(), self._buffer)
                action = ("update", self._buffer, matches)

            elif not self._capturing:
                pass  # not in capture mode, ignore

            elif event.name == "esc":
                self._buffer = ""
                self._capturing = False
                action = ("clear",)

            elif event.name == "backspace":
                if len(self._buffer) > 1:
                    self._buffer = self._buffer[:-1]
                    from template_loader import filter_templates
                    matches = filter_templates(self._get_templates(), self._buffer)
                    action = ("update", self._buffer, matches)
                else:
                    # Buffer would become empty — close picker
                    self._buffer = ""
                    self._capturing = False
                    action = ("clear",)

            elif event.name in MODIFIER_KEYS:
                pass  # ignore silently

            elif event.name in DISMISS_KEYS:
                self._buffer = ""
                self._capturing = False
                action = ("clear",)

            elif event.name and len(event.name) == 1:
                if len(self._buffer) >= 64:  # prevent runaway buffer
                    self._buffer = ""
                    self._capturing = False
                    action = ("clear",)
                else:
                    self._buffer += event.name
                    from template_loader import filter_templates
                    matches = filter_templates(self._get_templates(), self._buffer)
                    action = ("update", self._buffer, matches)

            elif event.name == "space":
                self._buffer += " "
                from template_loader import filter_templates
                matches = filter_templates(self._get_templates(), self._buffer)
                action = ("update", self._buffer, matches)

            else:
                # Unknown key — close picker
                self._buffer = ""
                self._capturing = False
                action = ("clear",)

        # Callbacks are invoked OUTSIDE the lock to avoid deadlocks
        if action is None:
            return
        if action[0] == "update":
            # Buffer content is NOT logged — could contain sensitive input
            log.debug("Buffer updated, matches=%d", len(action[2]))
            self._on_update(action[1], list(action[2]))
        elif action[0] == "clear":
            self._on_clear()
