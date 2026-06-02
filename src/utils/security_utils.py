"""
Advanced security utilities: memory locking, core dump prevention, screen capture blocking.
"""
import sys
import ctypes
from ctypes import wintypes


def lock_memory():
    """Best‑effort memory locking and core dump prevention."""
    try:
        if sys.platform == "win32":
            kernel32 = ctypes.windll.kernel32
            handle = wintypes.HANDLE(-1)
            min_size = 64 * 1024  # 64 KB minimum working set
            kernel32.SetProcessWorkingSetSize(handle, min_size, -1)
        elif sys.platform.startswith("linux"):
            import resource
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except Exception:
        pass


def disable_core_dumps():
    """Ensure no core dump is written (Linux)."""
    if sys.platform.startswith("linux"):
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        except Exception:
            pass


def set_screen_capture_blocking(hwnd: int, enable: bool):
    """Enable or disable screen capture protection on Windows (10 2004+)."""
    if sys.platform != "win32":
        return
    try:
        user32 = ctypes.windll.user32
        WDA_EXCLUDEFROMCAPTURE = 0x00000011
        WDA_MONITOR = 0x00000001
        flag = WDA_EXCLUDEFROMCAPTURE if enable else 0
        # Try modern flag first; fall back to older flag if it fails
        result = user32.SetWindowDisplayAffinity(hwnd, flag)
        if not result and enable:
            user32.SetWindowDisplayAffinity(hwnd, WDA_MONITOR)
    except Exception:
        pass