from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QComboBox,
    QDialogButtonBox, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt
from src.utils.config import Config

class CustomTemplateDialog(QDialog):
    """Dialog to manage custom field templates."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.templates = Config.get("custom_templates", [])
        self.setWindowTitle("Manage Custom Templates")
        self.setMinimumSize(500, 400)
        self.setStyleSheet("""
            QDialog { background: #1a1a2e; color: #e0e0e0; }
            QLabel, QComboBox { color: #e0e0e0; }
            QLineEdit { background: rgba(255,255,255,0.1); color: white; border: 1px solid #333; border-radius: 4px; padding: 5px; }
            QListWidget { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: white; }
            QPushButton { background: #0f9bff; border: none; border-radius: 8px; color: white; padding: 8px; font-weight: bold; }
            QPushButton:hover { background: #0091ea; }
        """)
        self._init_ui()
        self._refresh_list()

    def _init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Your Templates:"))

        self.template_list = QListWidget()
        layout.addWidget(self.template_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ New Template")
        add_btn.clicked.connect(self._add_template)
        btn_row.addWidget(add_btn)

        edit_btn = QPushButton("✏️ Edit Selected")
        edit_btn.clicked.connect(self._edit_template)
        btn_row.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self._delete_template)
        btn_row.addWidget(delete_btn)
        layout.addLayout(btn_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _refresh_list(self):
        self.template_list.clear()
        for t in self.templates:
            item = QListWidgetItem(f"{t['name']} ({len(t['fields'])} fields)")
            self.template_list.addItem(item)

    def _add_template(self):
        name, ok = QInputDialog.getText(self, "Template Name", "Enter a unique name:")
        if ok and name.strip():
            if len(self.templates) >= 50:
                QMessageBox.warning(self, "Limit Reached", "Maximum 50 templates allowed.")
                return
            if any(t['name'] == name.strip() for t in self.templates):
                QMessageBox.warning(self, "Error", "Template name already exists.")
                return
            new_template = {"name": name.strip(), "fields": []}
            self.templates.append(new_template)
            self._save_and_refresh()
            # Optionally immediately edit it
            self._edit_template(name.strip())

    def _edit_template(self, name=None):
        if name is None:
            current = self.template_list.currentItem()
            if not current:
                QMessageBox.warning(self, "No Selection", "Select a template to edit.")
                return
            name = current.text().split(" (")[0]
        t = next((t for t in self.templates if t['name'] == name), None)
        if not t:
            return
        # Open field editor for this template
        editor = TemplateFieldEditor(t, self)
        if editor.exec() == QDialog.DialogCode.Accepted:
            self._save_and_refresh()

    def _delete_template(self):
        current = self.template_list.currentItem()
        if not current:
            return
        name = current.text().split(" (")[0]
        reply = QMessageBox.question(self, "Delete", f"Delete template '{name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.templates = [t for t in self.templates if t['name'] != name]
            self._save_and_refresh()

    def _save_and_refresh(self):
        Config.set("custom_templates", self.templates)
        self._refresh_list()


class TemplateFieldEditor(QDialog):
    """Edit the fields of a single template."""
    def __init__(self, template: dict, parent=None):
        super().__init__(parent)
        self.template = template
        self.setWindowTitle(f"Edit Fields - {template['name']}")
        self.setMinimumSize(400, 300)
        self.setStyleSheet("""
            QDialog { background: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #e0e0e0; }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Fields:"))

        self.fields_list = QListWidget()
        self._populate_fields()
        layout.addWidget(self.fields_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Field")
        add_btn.clicked.connect(self._add_field)
        btn_row.addWidget(add_btn)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_field)
        btn_row.addWidget(remove_btn)
        layout.addLayout(btn_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _populate_fields(self):
        self.fields_list.clear()
        for f in self.template["fields"]:
            self.fields_list.addItem(f"{f['name']} ({f['type']})")

    def _add_field(self):
        name, ok = QInputDialog.getText(self, "Field Name", "Name:")
        if not ok or not name.strip():
            return
        if len(self.template["fields"]) >= 50:
            QMessageBox.warning(self, "Limit Reached", "Maximum 50 fields per template allowed.")
            return
        type_, ok = QInputDialog.getItem(self, "Field Type", "Type:", ["text", "password", "number", "date", "email"], 0, False)
        if not ok:
            return
        self.template["fields"].append({"name": name.strip(), "type": type_})
        self._populate_fields()

    def _remove_field(self):
        row = self.fields_list.currentRow()
        if row >= 0:
            self.template["fields"].pop(row)
            self._populate_fields()