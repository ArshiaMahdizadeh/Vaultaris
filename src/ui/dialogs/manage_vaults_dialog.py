from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog, QLineEdit,
    QMessageBox, QInputDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from src.core.vault_manager import VaultManager
from src.utils.config import Config

class ManageVaultsDialog(QDialog):
    def __init__(self, manager: VaultManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Manage Vaults")
        self.setMinimumSize(450, 300)
        self.setStyleSheet("""
            QDialog { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a2e, stop:1 #16213e); color: #e0e0e0; }
            QLabel { color: #e0e0e0; }
            QListWidget { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: white; }
            QPushButton { background: #0f9bff; border: none; border-radius: 8px; color: white; padding: 8px; font-weight: bold; }
            QPushButton:hover { background: #0091ea; }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Known Vaults:"))

        self.list_widget = QListWidget()
        self._refresh_list()
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self._open_vault)
        btn_row.addWidget(open_btn)

        create_btn = QPushButton("Create New")
        create_btn.clicked.connect(self._create_vault)
        btn_row.addWidget(create_btn)

        close_btn = QPushButton("Close Vault")
        close_btn.clicked.connect(self._close_vault)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _refresh_list(self):
        self.list_widget.clear()
        active = self.manager.active_path
        recent = Config.get("recent_vaults", [])
        for path in recent:
            item = QListWidgetItem(path)
            if path == active:
                item.setText(f"[ACTIVE] {path}")
                item.setForeground(Qt.GlobalColor.green)
            self.list_widget.addItem(item)

    def _open_vault(self):
        current = self.list_widget.currentItem()
        if not current:
            return
        path = current.text().replace("[ACTIVE] ", "")
        password, ok = QInputDialog.getText(self, "Password", "Enter master password:", echo=QLineEdit.EchoMode.Password)
        if ok and password:
            if self.manager.open_vault(path, password):
                QMessageBox.information(self, "Success", "Vault opened and activated.")
                self._refresh_list()
            else:
                QMessageBox.warning(self, "Error", "Wrong password or file error.")

    def _create_vault(self):
        path, _ = QFileDialog.getSaveFileName(self, "Create New Vault", "vault.enc", "Encrypted Vault (*.enc)")
        if not path:
            return
        password, ok = QInputDialog.getText(self, "Set Password", "Master password:", echo=QLineEdit.EchoMode.Password)
        if ok and password:
            if self.manager.create_vault(path, password):
                QMessageBox.information(self, "Created", "New vault created and active.")
                self._refresh_list()
            else:
                QMessageBox.warning(self, "Error", "Could not create vault.")

    def _close_vault(self):
        current = self.list_widget.currentItem()
        if not current:
            return
        path = current.text().replace("[ACTIVE] ", "")
        reply = QMessageBox.question(self, "Close Vault", f"Close vault '{path}'?\nYou will need to re-enter password to open it again.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.manager.close_vault(path)
            self._refresh_list()