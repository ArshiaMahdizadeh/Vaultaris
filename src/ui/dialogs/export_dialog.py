"""
Dialog to export vault data.
"""
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QComboBox, QLineEdit, QFormLayout, QMessageBox,
    QCheckBox, QDialogButtonBox, QWidget
)
from PyQt6.QtCore import Qt
from src.core.exporters import export_encrypted_json, export_plain_json, export_pdf_emergency_sheet

class ExportDialog(QDialog):
    def __init__(self, vault, parent=None):
        super().__init__(parent)
        self.vault = vault
        self.setWindowTitle("Export Vault")
        self.setMinimumSize(400, 300)
        self.setStyleSheet(self._style())
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Format selection
        layout.addWidget(QLabel("Export Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Encrypted JSON (.enc)", "Plain JSON (unsafe)", "PDF Emergency Sheet"])
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        layout.addWidget(self.format_combo)

        # Options
        self.include_totp_check = QCheckBox("Include TOTP secrets")
        self.include_totp_check.setChecked(True)
        layout.addWidget(self.include_totp_check)

        # Password for encrypted export
        self.password_widget = QWidget()
        pw_layout = QFormLayout()
        self.export_password_edit = QLineEdit()
        self.export_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.export_password_edit.setPlaceholderText("Set a password for the export")
        pw_layout.addRow("Password:", self.export_password_edit)
        self.password_widget.setLayout(pw_layout)
        layout.addWidget(self.password_widget)

        # File path
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Save to...")
        self.path_edit.setReadOnly(True)
        path_layout.addWidget(self.path_edit)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._export)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self._on_format_changed(0)

    def _on_format_changed(self, idx):
        fmt = self.format_combo.currentText()
        self.password_widget.setVisible(fmt != "Plain JSON (unsafe)")

    def _browse(self):
        fmt = self.format_combo.currentText()
        if "PDF" in fmt:
            filter_str = "PDF Files (*.pdf)"
        elif "JSON" in fmt:
            filter_str = "JSON Files (*.json)"
        else:
            filter_str = "Encrypted Vault (*.enc)"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save export", "", filter_str)
        if file_path:
            self.path_edit.setText(file_path)

    def _export(self):
        path = self.path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "Error", "Choose a save location.")
            return
        fmt = self.format_combo.currentText()
        # Optionally filter out TOTP if not checked
        items = self.vault.get_items()
        if not self.include_totp_check.isChecked():
            items = [cred.model_copy(update={'totp_secret': None}) for cred in items]

        try:
            if fmt == "Encrypted JSON (.enc)":
                password = self.export_password_edit.text()
                if not password:
                    QMessageBox.warning(self, "Password Required", "Enter a password to encrypt the export.")
                    return
                content = export_encrypted_json(items, password)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
            elif fmt == "Plain JSON (unsafe)":
                content = export_plain_json(items)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
            elif fmt == "PDF Emergency Sheet":
                password = self.export_password_edit.text()
                if not password:
                    QMessageBox.warning(self, "Password Required", "Set a password for the QR code content.")
                    return
                export_pdf_emergency_sheet(items, password, path)
            QMessageBox.information(self, "Export Successful", "Vault exported successfully.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _style(self):
        return """
        QDialog {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #1a1a2e, stop:1 #16213e);
            color: #e0e0e0;
        }
        QLabel { color: #e0e0e0; }
        QLineEdit, QComboBox {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 8px;
            padding: 8px;
            color: white;
        }
        QCheckBox { color: #e0e0e0; }
        QPushButton {
            background: #0f9bff;
            border: none;
            border-radius: 8px;
            color: white;
            padding: 8px;
            font-weight: bold;
        }
        QPushButton:hover { background: #0091ea; }
        """