from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QProgressBar, QApplication
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
from src.core.totp import get_totp_instance
import time

class TotpViewerDialog(QDialog):
    def __init__(self, secret: str, title: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"TOTP - {title}" if title else "TOTP Code")
        self.setFixedSize(300, 200)
        self.totp = get_totp_instance(secret)
        self.interval = self.totp.interval
        self._init_ui()
        self._update_code()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_code)
        self.timer.start(1000)

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        self.code_label = QLabel("------")
        self.code_label.setFont(QFont("Courier New", 36, QFont.Weight.Bold))
        self.code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.code_label)

        self.countdown_bar = QProgressBar()
        self.countdown_bar.setRange(0, self.interval)
        self.countdown_bar.setTextVisible(False)
        layout.addWidget(self.countdown_bar)

        copy_btn = QPushButton("📋 Copy Code")
        copy_btn.clicked.connect(self._copy_code)
        layout.addWidget(copy_btn)

        self.setLayout(layout)

    def _update_code(self):
        now = time.time()
        time_step = self.interval - (now % self.interval)
        self.countdown_bar.setValue(int(time_step))
        code = self.totp.now()
        self.code_label.setText(code)

    def _copy_code(self):
        code = self.code_label.text()
        QApplication.clipboard().setText(code)
        self.code_label.setText("Copied!")
        QTimer.singleShot(1000, lambda: self._update_code())