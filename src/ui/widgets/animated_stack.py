"""
AnimatedStack — a QStackedWidget replacement that cross-fades between pages.
Uses a QGraphicsOpacityEffect on the incoming widget so no pixel-buffer
compositing is needed, keeping it lightweight.
"""
from PyQt6.QtWidgets import QStackedWidget, QWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
    QAbstractAnimation, Qt
)


class AnimatedStack(QStackedWidget):
    """
    Drop-in replacement for QStackedWidget with a smooth fade transition.
    Duration and easing are configurable.
    """

    def __init__(self, parent=None, duration: int = 180):
        super().__init__(parent)
        self._duration = duration
        self._animating = False

    def setCurrentIndex(self, index: int):
        if index == self.currentIndex() or self._animating:
            super().setCurrentIndex(index)
            return

        old_widget = self.currentWidget()
        super().setCurrentIndex(index)
        new_widget = self.currentWidget()

        if old_widget is None or new_widget is None or old_widget is new_widget:
            return

        self._animating = True

        # ── Fade out old ──────────────────────────────────────────────────────
        old_effect = QGraphicsOpacityEffect(old_widget)
        old_widget.setGraphicsEffect(old_effect)

        fade_out = QPropertyAnimation(old_effect, b"opacity")
        fade_out.setDuration(self._duration)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)

        # ── Fade in new ───────────────────────────────────────────────────────
        new_effect = QGraphicsOpacityEffect(new_widget)
        new_widget.setGraphicsEffect(new_effect)
        new_effect.setOpacity(0.0)

        fade_in = QPropertyAnimation(new_effect, b"opacity")
        fade_in.setDuration(self._duration)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InCubic)

        # ── Run in parallel ───────────────────────────────────────────────────
        group = QParallelAnimationGroup(self)
        group.addAnimation(fade_out)
        group.addAnimation(fade_in)

        def _on_finished():
            self._animating = False
            old_widget.setGraphicsEffect(None)
            new_widget.setGraphicsEffect(None)

        group.finished.connect(_on_finished)
        group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
