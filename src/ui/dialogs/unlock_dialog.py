import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from src.core.vault_manager import VaultManager
from src.utils.config import Config


class UnlockDialog(QDialog):
    def __init__(self, manager: VaultManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Vaultaris")
        self.setFixedSize(440, 360)
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(16)

        # Logo / title
        logo = QLabel("🔐")
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

        unlock_btn = QPushButton("Unlock Vault")
        unlock_btn.setProperty("primary", True)
        unlock_btn.setStyle(unlock_btn.style())
        unlock_btn.setFixedHeight(42)
        unlock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        unlock_btn.clicked.connect(self._unlock)
        root.addWidget(unlock_btn)

        create_btn = QPushButton("Create New Vault")
        create_btn.setFixedHeight(38)
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self._create_new)
        root.addWidget(create_btn)

    def _unlock(self):
        password = self.master_password.text()
        if not password:
            self._error("Enter your master password")
            return

        # Duress password check
        if Config.get("duress_enabled", False) and password == Config.get("duress_password", ""):
            decoy_path = Config.get("decoy_vault_path", "")
            if decoy_path and os.path.exists(decoy_path):
                if self.manager.open_vault(decoy_path, password):
                    self.accept()
                    return
            self._error("Decoy vault not configured or cannot be opened")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Vault File", "", "Encrypted Vault (*.enc)"
        )
        if not file_path:
            return

        if self.manager.open_vault(file_path, password):
            self.accept()
        else:
            self._error("Wrong password or corrupted vault file")

    def _create_new(self):
        password = self.master_password.text()
        if len(password) < 8:
            self._error("Password must be at least 8 characters")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Create New Vault", "vault.enc", "Encrypted Vault (*.enc)"
        )
        if not file_path:
            return

        try:
            self.manager.create_vault(file_path, password)
            self.status_label.setStyleSheet("color: #3ecf8e; font-size: 12px; background: transparent;")
            self.status_label.setText("Vault created — click Unlock Vault to open it")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _error(self, msg: str):
        self.status_label.setStyleSheet("color: #f05c5c; font-size: 12px; background: transparent;")
        self.status_label.setText(msg)
