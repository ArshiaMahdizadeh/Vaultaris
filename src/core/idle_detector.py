import time
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QEvent
from PyQt6.QtWidgets import QApplication
from src.utils.config import Config

class IdleDetector(QObject):
    idle_timeout = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_activity = 0.0
        self._timeout_seconds = 5 * 60   # default 5 minutes
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_idle)
        self._active = False

    def start(self):
        if self._active:
            return
        self._active = True
        self._last_activity = time.time()
        # Enforce minimum 2 minutes (migration from old configs with 1 min)
        minutes = Config.get("idle_timeout_minutes", 5)
        if minutes < 2:
            minutes = 5
            Config.set("idle_timeout_minutes", 5)
        self.set_timeout_minutes(minutes)
        self._timer.start(1000)  # check every second
        QApplication.instance().installEventFilter(self)

    def stop(self):
        if not self._active:
            return
        self._active = False
        self._timer.stop()
        QApplication.instance().removeEventFilter(self)

    def reset(self):
        """Call this after user activity to restart the countdown."""
        self._last_activity = time.time()

    def set_timeout_minutes(self, minutes: int):
        # Ensure a sane minimum
        if minutes < 2:
            minutes = 5
        self._timeout_seconds = minutes * 60

    def eventFilter(self, obj, event):
        # Reset on any mouse / keyboard interaction
        if event.type() in (
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.MouseMove,
            QEvent.Type.KeyPress,
            QEvent.Type.KeyRelease,
            QEvent.Type.Wheel,
        ):
            self.reset()
        return False

    def _check_idle(self):
        if not self._active:
            return
        if Config.get("lock_on_idle", True):
            elapsed = time.time() - self._last_activity
            if elapsed >= self._timeout_seconds:
                self.idle_timeout.emit()
                self.reset()   # avoid repeated emissions until next full cycle