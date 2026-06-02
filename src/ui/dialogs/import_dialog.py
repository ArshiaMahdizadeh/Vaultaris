"""
Dialog to import credentials from files.
"""
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QComboBox, QLineEdit, QFormLayout, QMessageBox,
    QListWidget, QListWidgetItem, QCheckBox, QDialogButtonBox, QWidget
)
from PyQt6.QtCore import Qt
from src.models.credential import Credential
from src.core.importers import (
    import_csv, import_bitwarden_json, import_keepass, import_1password_csv
)

class ImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Passwords")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(self._style())
        self.credentials = []  # list of Credential
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["CSV (Generic)", "Bitwarden JSON", "KeePass KDBX", "1Password CSV"])
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)

        # File picker
        file_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Choose a file...")
        self.file_path_edit.setReadOnly(True)
        file_layout.addWidget(self.file_path_edit)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)

        # KeePass password (hidden unless KeePass selected)
        self.kdbx_password_edit = QLineEdit()
        self.kdbx_password_edit.setPlaceholderText("KeePass database password")
        self.kdbx_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.kdbx_password_edit.setVisible(False)
        layout.addWidget(self.kdbx_password_edit)

        # CSV column mapping (hidden unless CSV)
        self.csv_map_widget = QWidget()
        csv_layout = QFormLayout()
        self.title_col = QLineEdit("Title")
        self.url_col = QLineEdit("URL")
        self.username_col = QLineEdit("Username")
        self.password_col = QLineEdit("Password")
        self.notes_col = QLineEdit("Notes")
        self.totp_col = QLineEdit("OTPAuth")
        csv_layout.addRow("Title column:", self.title_col)
        csv_layout.addRow("URL column:", self.url_col)
        csv_layout.addRow("Username column:", self.username_col)
        csv_layout.addRow("Password column:", self.password_col)
        csv_layout.addRow("Notes column:", self.notes_col)
        csv_layout.addRow("TOTP column:", self.totp_col)
        self.csv_map_widget.setLayout(csv_layout)
        self.csv_map_widget.setVisible(False)
        layout.addWidget(self.csv_map_widget)

        # Preview list
        self.preview_list = QListWidget()
        self.preview_list.setVisible(False)
        layout.addWidget(self.preview_list)

        # Buttons
        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load Preview")
        self.load_btn.clicked.connect(self._load_preview)
        btn_layout.addWidget(self.load_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._import)
        buttons.rejected.connect(self.reject)
        btn_layout.addWidget(buttons)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _on_format_changed(self, idx):
        fmt = self.format_combo.currentText()
        self.csv_map_widget.setVisible(fmt == "CSV (Generic)")
        self.kdbx_password_edit.setVisible(fmt == "KeePass KDBX")

    def _browse_file(self):
        fmt = self.format_combo.currentText()
        filters = {
            "CSV (Generic)": "CSV Files (*.csv)",
            "Bitwarden JSON": "JSON Files (*.json)",
            "KeePass KDBX": "KeePass Files (*.kdbx)",
            "1Password CSV": "CSV Files (*.csv)"
        }
        file_path, _ = QFileDialog.getOpenFileName(self, "Select file", "", filters.get(fmt, ""))
        if file_path:
            self.file_path_edit.setText(file_path)

    def _load_preview(self):
        file_path = self.file_path_edit.text().strip()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", "Select a valid file.")
            return
        fmt = self.format_combo.currentText()
        try:
            if fmt == "CSV (Generic)":
                col_map = {
                    'title': self.title_col.text().strip() or None,
                    'url': self.url_col.text().strip() or None,
                    'username': self.username_col.text().strip() or None,
                    'password': self.password_col.text().strip() or None,
                    'notes': self.notes_col.text().strip() or None,
                    'totp_secret': self.totp_col.text().strip() or None
                }
                creds = import_csv(file_path, col_map)
            elif fmt == "Bitwarden JSON":
                creds = import_bitwarden_json(file_path)
            elif fmt == "KeePass KDBX":
                password = self.kdbx_password_edit.text()
                if not password:
                    QMessageBox.warning(self, "Password Required", "Enter the KeePass database password.")
                    return
                creds = import_keepass(file_path, password)
            elif fmt == "1Password CSV":
                creds = import_1password_csv(file_path)
            else:
                return
            self.credentials = creds
            self.preview_list.clear()
            for cred in creds[:50]:  # limit preview
                self.preview_list.addItem(QListWidgetItem(f"{cred.title} - {cred.username}"))
            self.preview_list.setVisible(True)
            QMessageBox.information(self, "Preview", f"Loaded {len(creds)} entries.")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    def _import(self):
        if not self.credentials:
            self.reject()
        self.accept()

    def get_credentials(self) -> list[Credential]:
        return self.credentials

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
        QPushButton {
            background: #0f9bff;
            border: none;
            border-radius: 8px;
            color: white;
            padding: 8px;
            font-weight: bold;
        }
        QPushButton:hover { background: #0091ea; }
        QListWidget {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            color: white;
        }
        """