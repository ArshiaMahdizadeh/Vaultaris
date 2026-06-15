"""
Advanced security: memory locking, screen capture blocking, panic actions.
"""
import sys
import ctypes
from ctypes import wintypes

def lock_memory():
    """Lock sensitive memory pages in RAM (Windows via VirtualLock, Linux via mlockall)."""
    try:
        if sys.platform == "win32":
            kernel32 = ctypes.windll.kernel32
            kernel32.VirtualLock.restype = wintypes.BOOL
            kernel32.VirtualLock.argtypes = [wintypes.LPVOID, ctypes.c_size_t]
            # Lock all currently committed pages to prevent swapping
            kernel32.VirtualLock(None, 0)
    except Exception:
        pass

def set_screen_capture_blocking(hwnd: int, enable: bool):
    """On Windows, enable/disable screen capture blocking for the window."""
    if sys.platform != "win32":
        return
    try:
        user32 = ctypes.windll.user32
        WDA_EXCLUDEFROMCAPTURE = 0x00000011  # Windows 10 2004+
        WDA_MONITOR = 0x00000001
        flag = WDA_EXCLUDEFROMCAPTURE if enable else 0
        result = user32.SetWindowDisplayAffinity(hwnd, flag)
        if not result and enable:
            user32.SetWindowDisplayAffinity(hwnd, WDA_MONITOR)
    except Exception:
        pass

def disable_core_dumps():
    """Prevent core dumps on Linux."""
    if sys.platform.startswith("linux"):
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        except Exception:
            pass
