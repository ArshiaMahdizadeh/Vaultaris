import json
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog, QLineEdit,
    QMessageBox, QInputDialog, QDialogButtonBox, QProgressBar
)
from PyQt6.QtCore import Qt
from src.core.vault_manager import VaultManager
from src.utils.config import Config
from src.utils.worker import VaultWorker


class ManageVaultsDialog(QDialog):
    def __init__(self, manager: VaultManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Manage Vaults")
        self.setMinimumSize(450, 300)
        self._worker = None
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
        self.open_btn = QPushButton("Open")
        self.open_btn.clicked.connect(self._open_vault)
        btn_row.addWidget(self.open_btn)

        self.create_btn = QPushButton("Create New")
        self.create_btn.clicked.connect(self._create_vault)
        btn_row.addWidget(self.create_btn)

        self.close_btn = QPushButton("Close Vault")
        self.close_btn.clicked.connect(self._close_vault)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

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
        layout.addWidget(self.progress_bar)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _set_loading(self, loading: bool):
        self.open_btn.setEnabled(not loading)
        self.create_btn.setEnabled(not loading)
        self.close_btn.setEnabled(not loading)
        self.list_widget.setEnabled(not loading)
        self.progress_bar.setVisible(loading)

    def _refresh_list(self):
        self.list_widget.clear()
        active = self.manager.active_path
        recent = Config.get("recent_vaults", [])
        for entry in recent:
            if isinstance(entry, dict):
                display = entry.get("basename", entry.get("path_hash", "?"))
            else:
                display = entry
            item = QListWidgetItem(display)
            if display == active or (isinstance(entry, dict) and entry.get("path_hash", "") in (active or "")):
                item.setText(f"[ACTIVE] {display}")
                item.setForeground(Qt.GlobalColor.green)
            self.list_widget.addItem(item)

    def _get_vault_path(self, entry) -> str | None:
        if isinstance(entry, dict):
            path_hash = entry.get("path_hash", "")
            basename = entry.get("basename", "")
            for candidate in Config.get("recent_vaults", []):
                if isinstance(candidate, str) and os.path.basename(candidate) == basename:
                    return candidate
            return None
        return entry

    def _validate_vault_file(self, path: str) -> bool:
        try:
            with open(path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
            meta = json.loads(first_line)
            return "salt" in meta and "verifier" in meta
        except (json.JSONDecodeError, FileNotFoundError, KeyError):
            return False

    def _open_vault(self):
        current = self.list_widget.currentItem()
        if not current:
            return
        display = current.text().replace("[ACTIVE] ", "")
        recent = Config.get("recent_vaults", [])
        entry = None
        for r in recent:
            if isinstance(r, dict) and r.get("basename") == display:
                entry = r
                break
            elif r == display:
                entry = r
                break
        if entry is None:
            QMessageBox.warning(self, "Error", "Could not resolve vault path.")
            return
        path = self._get_vault_path(entry)
        if not path:
            QMessageBox.warning(self, "Error", "Vault file not found.")
            return
        if not self._validate_vault_file(path):
            QMessageBox.warning(self, "Invalid Vault", "The file does not appear to be a valid Vaultaris vault.")
            return
        password, ok = QInputDialog.getText(self, "Password", "Enter master password:", echo=QLineEdit.EchoMode.Password)
        if ok and password:
            self._set_loading(True)
            self._pending_password = password
            self._worker = VaultWorker(self.manager.open_vault, path, password)
            self._worker.progress.connect(self._on_progress)
            self._worker.finished.connect(self._on_open_result)
            self._worker.start()

    def _on_open_result(self, success, error_msg):
        self._set_loading(False)
        self._worker = None
        pw = self._pending_password
        self._pending_password = ""
        if success:
            QMessageBox.information(self, "Success", "Vault opened and activated.")
            self._refresh_list()
        else:
            QMessageBox.warning(self, "Error", error_msg or "Wrong password or file error.")

    def _create_vault(self):
        path, _ = QFileDialog.getSaveFileName(self, "Create New Vault", "vault.enc", "Encrypted Vault (*.enc)")
        if not path:
            return
        password, ok = QInputDialog.getText(self, "Set Password", "Master password:", echo=QLineEdit.EchoMode.Password)
        if ok and password:
            self._set_loading(True)
            self._pending_password = password
            self._worker = VaultWorker(self.manager.create_vault, path, password)
            self._worker.progress.connect(self._on_progress)
            self._worker.finished.connect(self._on_create_result)
            self._worker.start()

    def _on_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)

    def _on_create_result(self, success, error_msg):
        self._set_loading(False)
        self._worker = None
        self._pending_password = ""
        if success:
            QMessageBox.information(self, "Created", "New vault created and active.")
            self._refresh_list()
        else:
            QMessageBox.warning(self, "Error", error_msg or "Could not create vault.")

    def _close_vault(self):
        current = self.list_widget.currentItem()
        if not current:
            return
        display = current.text().replace("[ACTIVE] ", "")
        reply = QMessageBox.question(self, "Close Vault", f"Close vault '{display}'?\nYou will need to re-enter password to open it again.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.manager.close_vault(display)
            self._refresh_list()

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(3000)
        super().closeEvent(event)
