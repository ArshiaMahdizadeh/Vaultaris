from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QProgressBar, QPushButton, QApplication, QFrame
)
from PyQt6.QtCore import QTimer, Qt, QSize
from PyQt6.QtGui import QFont
from src.core.vault_manager import VaultManager
from src.core.totp import get_totp_instance, generate_totp
import time


class TotpCard(QFrame):
    def __init__(self, item, copy_callback, parent=None):
        super().__init__(parent)
        self.totp_secret = item.totp_secret
        self._copy_cb = copy_callback

        self.setObjectName("TotpCard")
        self.setStyleSheet("""
            QFrame#TotpCard {
                background-color: #13131e;
                border: 1px solid #2c2c42;
                border-radius: 10px;
            }
        """)
        self.setMinimumHeight(72)

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 12, 16, 12)
        row.setSpacing(16)

        # Title + username
        info = QVBoxLayout()
        info.setSpacing(2)
        name_lbl = QLabel(item.title)
        name_lbl.setStyleSheet("color: #dde1f0; font-size: 13px; font-weight: 600; background: transparent;")
        info.addWidget(name_lbl)
        if item.username:
            user_lbl = QLabel(item.username)
            user_lbl.setStyleSheet("color: #6666888; font-size: 11px; background: transparent;")
            info.addWidget(user_lbl)
        row.addLayout(info, stretch=1)

        # Code
        self.code_label = QLabel("------")
        code_font = QFont("Cascadia Code", 22, QFont.Weight.Bold)
        code_font.setFamilies(["Cascadia Code", "Fira Code", "Courier New"])
        self.code_label.setFont(code_font)
        self.code_label.setStyleSheet("color: #4f8ef7; background: transparent; letter-spacing: 4px;")
        self.code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self.code_label)

        # Progress + copy
        right = QVBoxLayout()
        right.setSpacing(6)
        right.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setRange(0, 30)
        self.progress.setTextVisible(False)
        self.progress.setFixedWidth(80)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet("""
            QProgressBar { background: #2c2c42; border: none; border-radius: 3px; }
            QProgressBar::chunk { background: #4f8ef7; border-radius: 3px; }
        """)
        right.addWidget(self.progress)

        copy_btn = QPushButton("Copy")
        copy_btn.setFixedHeight(28)
        copy_btn.setFixedWidth(64)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(lambda: self._copy_cb(self.totp_secret))
        right.addWidget(copy_btn)

        row.addLayout(right)


class TotpWidget(QWidget):
    def __init__(self, manager: VaultManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._init_ui()
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_codes)
        self._timer.start(1000)

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(16)

        title = QLabel("Authenticator")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #dde1f0;")
        root.addWidget(title)

        sub = QLabel("TOTP codes update every 30 seconds")
        sub.setStyleSheet("color: #6666888; font-size: 12px;")
        root.addWidget(sub)

        self.totp_list = QListWidget()
        self.totp_list.setSpacing(4)
        root.addWidget(self.totp_list, stretch=1)

        self._populate_list()

    def _populate_list(self):
        self.totp_list.clear()
        try:
            items = self.manager.get_items() if self.manager.active_vault else []
        except RuntimeError:
            return

        has_totp = False
        for item in items:
            if item.totp_secret:
                has_totp = True
                card = TotpCard(item, self._copy_code)
                li = QListWidgetItem()
                li.setSizeHint(card.sizeHint() + QSize(0, 6))
                self.totp_list.addItem(li)
                self.totp_list.setItemWidget(li, card)

        if not has_totp:
            empty = QLabel("No TOTP secrets found.\nAdd a TOTP secret to a password item to see codes here.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #6666888; font-size: 13px;")
            li = QListWidgetItem()
            li.setSizeHint(QSize(0, 120))
            self.totp_list.addItem(li)
            self.totp_list.setItemWidget(li, empty)

    def _update_codes(self):
        now = time.time()
        for i in range(self.totp_list.count()):
            li = self.totp_list.item(i)
            widget = self.totp_list.itemWidget(li)
            if widget and hasattr(widget, "totp_secret"):
                try:
                    totp = get_totp_instance(widget.totp_secret)
                    widget.code_label.setText(totp.now())
                    remaining = int(totp.interval - now % totp.interval)
                    widget.progress.setMaximum(int(totp.interval))
                    widget.progress.setValue(remaining)
                    # Colour warning when < 5 s
                    color = "#f05c5c" if remaining <= 5 else "#4f8ef7"
                    widget.code_label.setStyleSheet(
                        f"color: {color}; background: transparent; letter-spacing: 4px;"
                    )
                    widget.progress.setStyleSheet(f"""
                        QProgressBar {{ background: #2c2c42; border: none; border-radius: 3px; }}
                        QProgressBar::chunk {{ background: {color}; border-radius: 3px; }}
                    """)
                except Exception:
                    widget.code_label.setText("Error")

    def _copy_code(self, secret: str):
        try:
            QApplication.clipboard().setText(generate_totp(secret))
        except Exception:
            pass
