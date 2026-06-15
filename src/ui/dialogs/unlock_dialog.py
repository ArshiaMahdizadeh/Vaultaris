import os
import random
import time
import base64
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QFrame,
    QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from src.core.vault_manager import VaultManager
from src.core.crypto import verify_password
from src.utils.config import Config
from src.utils.worker import VaultWorker


class UnlockDialog(QDialog):
    def __init__(self, manager: VaultManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Vaultaris")
        self.setFixedSize(440, 360)
        self._worker = None
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(16)

        logo = QLabel("\U0001f510")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size: 40px; background: transparent;")
        root.addWidget(logo)

        title = QLabel("Vaultaris")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #dde1f0; background: transparent;")
        root.addWidget(title)

        sub = QLabel("Enter your master password to continue")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #6666888; font-size: 12px; background: transparent;")
        root.addWidget(sub)

        root.addSpacing(4)

        self.master_password = QLineEdit()
        self.master_password.setPlaceholderText("Master password")
        self.master_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.master_password.setFixedHeight(42)
        self.master_password.returnPressed.connect(self._unlock)
        root.addWidget(self.master_password)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #f05c5c; font-size: 12px; background: transparent;")
        self.status_label.setFixedHeight(18)
        root.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: none; background: rgba(255,255,255,0.1); border-radius: 2px; }
            QProgressBar::chunk { background: #0f9bff; border-radius: 2px; }
        """)
        root.addWidget(self.progress_bar)

        self.unlock_btn = QPushButton("Unlock Vault")
        self.unlock_btn.setProperty("primary", True)
        self.unlock_btn.setStyle(self.unlock_btn.style())
        self.unlock_btn.setFixedHeight(42)
        self.unlock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.unlock_btn.clicked.connect(self._unlock)
        root.addWidget(self.unlock_btn)

        self.create_btn = QPushButton("Create New Vault")
        self.create_btn.setFixedHeight(38)
        self.create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_btn.clicked.connect(self._create_new)
        root.addWidget(self.create_btn)

    def _set_loading(self, loading: bool, message: str = ""):
        self.master_password.setEnabled(not loading)
        self.unlock_btn.setEnabled(not loading)
        self.create_btn.setEnabled(not loading)
        self.progress_bar.setVisible(loading)
        if loading:
            self.status_label.setStyleSheet("color: #0f9bff; font-size: 12px; background: transparent;")
            self.status_label.setText(message or "Processing...")
        else:
            self.status_label.setText("")

    def _unlock(self):
        password = self.master_password.text()
        if not password:
            self._error("Enter your master password")
            return

        duress_resolved = False

        if Config.get("duress_enabled", False):
            stored_hash_b64 = Config.get("duress_password_hash", "")
            stored_salt_b64 = Config.get("duress_password_salt", "")
            if stored_hash_b64 and stored_salt_b64:
                stored_hash = base64.b64decode(stored_hash_b64)
                stored_salt = base64.b64decode(stored_salt_b64)
                if verify_password(password, stored_salt, stored_hash):
                    decoy_path = Config.get("decoy_vault_path", "")
                    if decoy_path and os.path.exists(decoy_path):
                        self._set_loading(True, "Opening decoy vault...")
                        self._worker = VaultWorker(self.manager.open_vault, decoy_path, password)
                        self._worker.progress.connect(self._on_progress)
                        self._worker.finished.connect(self._on_open_result)
                        self._worker.start()
                        return
                    time.sleep(random.uniform(0.1, 0.5))
                    duress_resolved = True

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Vault File", "", "Encrypted Vault (*.enc)"
        )
        if not file_path:
            self.master_password.clear()
            return

        self._set_loading(True, "Deriving key, please wait...")
        self._worker = VaultWorker(self.manager.open_vault, file_path, password)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_open_result)
        self._worker.start()

    def _on_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        if msg:
            self.status_label.setStyleSheet("color: #0f9bff; font-size: 12px; background: transparent;")
            self.status_label.setText(msg)

    def _on_open_result(self, success, error_msg):
        self._set_loading(False)
        self._worker = None
        if success:
            self.master_password.clear()
            self.accept()
        else:
            self._error(error_msg or "Wrong password or corrupted vault file")

    def _create_new(self):
        password = self.master_password.text()
        if len(password) < 8:
            self._error("Password must be at least 8 characters")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Create New Vault", "vault.enc", "Encrypted Vault (*.enc)"
        )
        if not file_path:
            self.master_password.clear()
            return

        self._set_loading(True, "Creating vault, please wait...")
        self._worker = VaultWorker(self.manager.create_vault, file_path, password)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_create_result)
        self._worker.start()

    def _on_create_result(self, success, error_msg):
        self._set_loading(False)
        self._worker = None
        if success:
            self.master_password.clear()
            self.status_label.setStyleSheet("color: #3ecf8e; font-size: 12px; background: transparent;")
            self.status_label.setText("Vault created — click Unlock Vault to open it")
        else:
            self._error(error_msg or "Failed to create vault")

    def _error(self, msg: str):
        self.status_label.setStyleSheet("color: #f05c5c; font-size: 12px; background: transparent;")
        self.status_label.setText(msg)

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(3000)
        super().closeEvent(event)
