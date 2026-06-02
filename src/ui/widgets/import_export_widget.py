from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QComboBox, QLineEdit, QMessageBox, QFrame, QTabWidget
)
from PyQt6.QtCore import Qt
from src.core.vault_manager import VaultManager
from src.core.importers import import_csv, import_bitwarden_json, import_keepass, import_1password_csv
from src.core.exporters import export_encrypted_json, export_plain_json, export_pdf_emergency_sheet


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color: #8888aa; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
    return lbl


def _card() -> QFrame:
    f = QFrame()
    f.setStyleSheet("""
        QFrame {
            background-color: #13131e;
            border: 1px solid #2c2c42;
            border-radius: 10px;
        }
    """)
    return f


class ImportExportWidget(QWidget):
    def __init__(self, manager: VaultManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(16)

        title = QLabel("Import / Export")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #dde1f0;")
        root.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._build_import_tab(), "Import")
        tabs.addTab(self._build_export_tab(), "Export")
        root.addWidget(tabs, stretch=1)

    # ── Import tab ────────────────────────────────────────────────────────────
    def _build_import_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(_section_label("SOURCE FORMAT"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["CSV (Generic)", "Bitwarden JSON", "KeePass KDBX", "1Password CSV"])
        self.format_combo.currentIndexChanged.connect(self._on_import_format_changed)
        layout.addWidget(self.format_combo)

        layout.addWidget(_section_label("FILE"))
        file_row = QHBoxLayout()
        file_row.setSpacing(8)
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Choose a file…")
        self.file_path_edit.setReadOnly(True)
        file_row.addWidget(self.file_path_edit, stretch=1)
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedHeight(36)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_import)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        self.kdbx_password_edit = QLineEdit()
        self.kdbx_password_edit.setPlaceholderText("KeePass database password")
        self.kdbx_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.kdbx_password_edit.setVisible(False)
        layout.addWidget(self.kdbx_password_edit)

        layout.addStretch()

        import_btn = QPushButton("Import into Vault")
        import_btn.setProperty("primary", True)
        import_btn.setStyle(import_btn.style())
        import_btn.setFixedHeight(40)
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.clicked.connect(self._do_import)
        layout.addWidget(import_btn)

        return page

    def _on_import_format_changed(self):
        self.kdbx_password_edit.setVisible(
            self.format_combo.currentText() == "KeePass KDBX"
        )

    def _browse_import(self):
        fmt = self.format_combo.currentText()
        filters = {
            "CSV (Generic)":   "CSV Files (*.csv)",
            "Bitwarden JSON":  "JSON Files (*.json)",
            "KeePass KDBX":    "KeePass Files (*.kdbx)",
            "1Password CSV":   "CSV Files (*.csv)",
        }
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "", filters.get(fmt, ""))
        if path:
            self.file_path_edit.setText(path)

    def _do_import(self):
        path = self.file_path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "No File", "Select a file first.")
            return
        if not self.manager.active_vault:
            QMessageBox.warning(self, "Locked", "Open a vault before importing.")
            return
        fmt = self.format_combo.currentText()
        try:
            if fmt == "CSV (Generic)":
                col_map = {"title": "Title", "url": "URL", "username": "Username",
                           "password": "Password", "notes": "Notes", "totp_secret": "OTPAuth"}
                creds = import_csv(path, col_map)
            elif fmt == "Bitwarden JSON":
                creds = import_bitwarden_json(path)
            elif fmt == "KeePass KDBX":
                pwd = self.kdbx_password_edit.text()
                if not pwd:
                    QMessageBox.warning(self, "Password Required", "Enter the KeePass password.")
                    return
                creds = import_keepass(path, pwd)
            elif fmt == "1Password CSV":
                creds = import_1password_csv(path)
            else:
                return

            reply = QMessageBox.question(
                self, "Confirm Import",
                f"Add {len(creds)} item(s) to the active vault?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                for c in creds:
                    self.manager.add_item(c)
                QMessageBox.information(self, "Done", f"{len(creds)} item(s) imported.")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    # ── Export tab ────────────────────────────────────────────────────────────
    def _build_export_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(_section_label("FORMAT"))
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems([
            "Encrypted JSON (.enc)",
            "Plain JSON (unencrypted)",
            "PDF Emergency Sheet",
        ])
        self.export_format_combo.currentIndexChanged.connect(self._on_export_format_changed)
        layout.addWidget(self.export_format_combo)

        layout.addWidget(_section_label("EXPORT PASSWORD"))
        self.export_password_edit = QLineEdit()
        self.export_password_edit.setPlaceholderText("Password to protect the export")
        self.export_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.export_password_edit)

        layout.addWidget(_section_label("DESTINATION"))
        dest_row = QHBoxLayout()
        dest_row.setSpacing(8)
        self.export_path_edit = QLineEdit()
        self.export_path_edit.setPlaceholderText("Save to…")
        self.export_path_edit.setReadOnly(True)
        dest_row.addWidget(self.export_path_edit, stretch=1)
        browse_exp_btn = QPushButton("Browse")
        browse_exp_btn.setFixedHeight(36)
        browse_exp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_exp_btn.clicked.connect(self._browse_export)
        dest_row.addWidget(browse_exp_btn)
        layout.addLayout(dest_row)

        layout.addStretch()

        export_btn = QPushButton("Export Vault")
        export_btn.setProperty("primary", True)
        export_btn.setStyle(export_btn.style())
        export_btn.setFixedHeight(40)
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._do_export)
        layout.addWidget(export_btn)

        # Initial state
        self._on_export_format_changed()
        return page

    def _on_export_format_changed(self):
        fmt = self.export_format_combo.currentText()
        needs_pwd = "Plain JSON" not in fmt
        self.export_password_edit.setEnabled(needs_pwd)
        self.export_password_edit.setPlaceholderText(
            "Password to protect the export" if needs_pwd else "Not required for plain JSON"
        )

    def _browse_export(self):
        fmt = self.export_format_combo.currentText()
        if "PDF" in fmt:
            filt = "PDF Files (*.pdf)"
        elif "Plain" in fmt:
            filt = "JSON Files (*.json)"
        else:
            filt = "Encrypted Vault (*.enc)"
        path, _ = QFileDialog.getSaveFileName(self, "Save Export", "", filt)
        if path:
            self.export_path_edit.setText(path)

    def _do_export(self):
        path = self.export_path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "No Destination", "Choose a save location first.")
            return
        if not self.manager.active_vault:
            QMessageBox.warning(self, "Locked", "Open a vault before exporting.")
            return
        items = self.manager.get_items()
        fmt = self.export_format_combo.currentText()
        pwd = self.export_password_edit.text()
        try:
            if fmt == "Encrypted JSON (.enc)":
                if not pwd:
                    QMessageBox.warning(self, "Password Required", "Enter an export password.")
                    return
                content = export_encrypted_json(items, pwd)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
            elif fmt == "Plain JSON (unencrypted)":
                reply = QMessageBox.warning(
                    self, "Security Warning",
                    "Plain JSON export contains unencrypted passwords.\nContinue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
                content = export_plain_json(items)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
            elif fmt == "PDF Emergency Sheet":
                if not pwd:
                    QMessageBox.warning(self, "Password Required", "Enter an export password.")
                    return
                export_pdf_emergency_sheet(items, pwd, path)
            QMessageBox.information(self, "Export Complete", "Vault exported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
