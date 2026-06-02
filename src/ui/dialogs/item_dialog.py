from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QFormLayout, QDialogButtonBox, QComboBox, QStackedWidget,
    QWidget, QTextEdit, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt
from src.models.item import Item, ItemType
from src.ui.dialogs.generator_dialog import GeneratorDialog
from src.ui.dialogs.totp_setup_dialog import TotpSetupDialog
from src.ui.dialogs.custom_template_dialog import CustomTemplateDialog
from src.utils.config import Config
import time
import uuid

class ItemDialog(QDialog):
    def __init__(self, parent=None, item: Item = None):
        super().__init__(parent)
        self.item = item or Item()
        self.templates = Config.get("custom_templates", [])
        self.setWindowTitle("Edit Item" if item else "Add Item")
        self.setMinimumWidth(500)
        self._init_ui()
        self._load_item()

    def _init_ui(self):
        main_layout = QVBoxLayout()

        # Type selector
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        for t in ItemType:
            self.type_combo.addItem(t.value.capitalize(), t)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        main_layout.addLayout(type_layout)

        # Stacked widget
        self.stacked = QStackedWidget()
        self._build_password_page()
        self._build_note_page()
        self._build_credit_card_page()
        self._build_identity_page()
        self._build_wifi_page()
        self._build_license_page()
        self._build_crypto_page()
        self._build_custom_page()
        main_layout.addWidget(self.stacked)

        # TOTP row (only for password)
        totp_layout = QHBoxLayout()
        self.totp_secret_edit = QLineEdit(self.item.totp_secret or "")
        self.totp_secret_edit.setPlaceholderText("No TOTP secret set")
        self.totp_secret_edit.setReadOnly(True)
        totp_layout.addWidget(self.totp_secret_edit)
        setup_totp_btn = QPushButton("⚙️ Set up")
        setup_totp_btn.clicked.connect(self._setup_totp)
        totp_layout.addWidget(setup_totp_btn)
        clear_totp_btn = QPushButton("🗑️ Clear")
        clear_totp_btn.clicked.connect(lambda: self.totp_secret_edit.clear())
        totp_layout.addWidget(clear_totp_btn)
        main_layout.addLayout(totp_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        self.setLayout(main_layout)
        self._on_type_changed(0)

    # ---------------- Build pages ----------------
    def _build_password_page(self):
        page = QWidget()
        form = QFormLayout()
        self.title_edit = QLineEdit()
        form.addRow("Title:", self.title_edit)
        self.url_edit = QLineEdit()
        form.addRow("URL:", self.url_edit)
        self.username_edit = QLineEdit()
        form.addRow("Username:", self.username_edit)
        pw_layout = QHBoxLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pw_layout.addWidget(self.password_edit)
        gen_btn = QPushButton("🎲")
        gen_btn.clicked.connect(self._generate_password)
        pw_layout.addWidget(gen_btn)
        form.addRow("Password:", pw_layout)
        self.notes_edit = QTextEdit()
        form.addRow("Notes:", self.notes_edit)
        page.setLayout(form)
        self.stacked.addWidget(page)

    def _build_note_page(self):
        page = QWidget()
        form = QFormLayout()
        self.note_title_edit = QLineEdit()
        form.addRow("Title:", self.note_title_edit)
        self.note_notes_edit = QTextEdit()
        form.addRow("Note (Markdown):", self.note_notes_edit)
        page.setLayout(form)
        self.stacked.addWidget(page)

    def _build_credit_card_page(self):
        page = QWidget()
        form = QFormLayout()
        self.cc_title_edit = QLineEdit()
        form.addRow("Title:", self.cc_title_edit)
        self.cc_number_edit = QLineEdit()
        form.addRow("Card Number:", self.cc_number_edit)
        self.cc_holder_edit = QLineEdit()
        form.addRow("Cardholder:", self.cc_holder_edit)
        self.cc_expiry_edit = QLineEdit()
        form.addRow("Expiry (MM/YY):", self.cc_expiry_edit)
        self.cc_cvv_edit = QLineEdit()
        self.cc_cvv_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("CVV:", self.cc_cvv_edit)
        self.cc_notes_edit = QTextEdit()
        form.addRow("Notes:", self.cc_notes_edit)
        page.setLayout(form)
        self.stacked.addWidget(page)

    def _build_identity_page(self):
        page = QWidget()
        form = QFormLayout()
        self.id_title_edit = QLineEdit()
        form.addRow("Title:", self.id_title_edit)
        self.id_firstname_edit = QLineEdit()
        form.addRow("First Name:", self.id_firstname_edit)
        self.id_lastname_edit = QLineEdit()
        form.addRow("Last Name:", self.id_lastname_edit)
        self.id_email_edit = QLineEdit()
        form.addRow("Email:", self.id_email_edit)
        self.id_phone_edit = QLineEdit()
        form.addRow("Phone:", self.id_phone_edit)
        self.id_address_edit = QTextEdit()
        form.addRow("Address:", self.id_address_edit)
        self.id_notes_edit = QTextEdit()
        form.addRow("Notes:", self.id_notes_edit)
        page.setLayout(form)
        self.stacked.addWidget(page)

    def _build_wifi_page(self):
        page = QWidget()
        form = QFormLayout()
        self.wifi_title_edit = QLineEdit()
        form.addRow("Title:", self.wifi_title_edit)
        self.wifi_ssid_edit = QLineEdit()
        form.addRow("SSID:", self.wifi_ssid_edit)
        self.wifi_password_edit = QLineEdit()
        self.wifi_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Password:", self.wifi_password_edit)
        self.wifi_security_edit = QLineEdit()
        form.addRow("Security:", self.wifi_security_edit)
        self.wifi_notes_edit = QTextEdit()
        form.addRow("Notes:", self.wifi_notes_edit)
        page.setLayout(form)
        self.stacked.addWidget(page)

    def _build_license_page(self):
        page = QWidget()
        form = QFormLayout()
        self.lic_title_edit = QLineEdit()
        form.addRow("Title:", self.lic_title_edit)
        self.lic_vendor_edit = QLineEdit()
        form.addRow("Vendor:", self.lic_vendor_edit)
        self.lic_key_edit = QLineEdit()
        self.lic_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("License Key:", self.lic_key_edit)
        self.lic_notes_edit = QTextEdit()
        form.addRow("Notes:", self.lic_notes_edit)
        page.setLayout(form)
        self.stacked.addWidget(page)

    def _build_crypto_page(self):
        page = QWidget()
        form = QFormLayout()
        self.crypto_title_edit = QLineEdit()
        form.addRow("Title:", self.crypto_title_edit)
        self.crypto_wallet_type_edit = QLineEdit()
        form.addRow("Wallet Type:", self.crypto_wallet_type_edit)
        self.crypto_seed_phrase_edit = QTextEdit()
        form.addRow("Seed Phrase:", self.crypto_seed_phrase_edit)
        self.crypto_notes_edit = QTextEdit()
        form.addRow("Notes:", self.crypto_notes_edit)
        page.setLayout(form)
        self.stacked.addWidget(page)

    def _build_custom_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Template:"))
        self.custom_template_combo = QComboBox()
        self.custom_template_combo.addItem("None", None)
        for t in self.templates:
            self.custom_template_combo.addItem(t["name"], t)
        self.custom_template_combo.currentIndexChanged.connect(self._on_custom_template_changed)
        template_layout.addWidget(self.custom_template_combo)

        manage_btn = QPushButton("Manage Templates")
        manage_btn.clicked.connect(self._manage_templates)
        template_layout.addWidget(manage_btn)
        layout.addLayout(template_layout)

        # Dynamic form area
        self.custom_form_widget = QWidget()
        self.custom_form_layout = QFormLayout()
        self.custom_form_widget.setLayout(self.custom_form_layout)
        layout.addWidget(self.custom_form_widget)

        self.custom_notes_edit = QTextEdit()
        layout.addWidget(QLabel("Notes:"))
        layout.addWidget(self.custom_notes_edit)

        page.setLayout(layout)
        self.stacked.addWidget(page)

    def _on_custom_template_changed(self, idx):
        # Clear old dynamic fields
        while self.custom_form_layout.rowCount() > 0:
            self.custom_form_layout.removeRow(0)
        self.custom_fields_widgets = {}  # name -> QWidget

        template = self.custom_template_combo.itemData(idx)
        if template is None:
            return
        for field in template["fields"]:
            name = field["name"]
            ftype = field["type"]
            if ftype in ("password",):
                widget = QLineEdit()
                widget.setEchoMode(QLineEdit.EchoMode.Password)
            elif ftype in ("text", "email", "date"):
                widget = QLineEdit()
            elif ftype == "number":
                widget = QLineEdit()
            else:
                widget = QLineEdit()
            self.custom_form_layout.addRow(name + ":", widget)
            self.custom_fields_widgets[name] = widget

    def _manage_templates(self):
        dialog = CustomTemplateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload templates from config
            self.templates = Config.get("custom_templates", [])
            # Refresh the combo
            self.custom_template_combo.blockSignals(True)
            self.custom_template_combo.clear()
            self.custom_template_combo.addItem("None", None)
            for t in self.templates:
                self.custom_template_combo.addItem(t["name"], t)
            self.custom_template_combo.blockSignals(False)
            # Re-apply current template if any
            current_idx = self.custom_template_combo.findText(self.item.custom_template_id or "")
            if current_idx >= 0:
                self.custom_template_combo.setCurrentIndex(current_idx)
            else:
                self._on_custom_template_changed(self.custom_template_combo.currentIndex())

    # ---------------- Type switching ----------------
    def _on_type_changed(self, idx):
        item_type = self.type_combo.currentData()
        type_index_map = {
            ItemType.PASSWORD: 0,
            ItemType.NOTE: 1,
            ItemType.CREDIT_CARD: 2,
            ItemType.IDENTITY: 3,
            ItemType.WIFI: 4,
            ItemType.LICENSE: 5,
            ItemType.CRYPTO_SEED: 6,
            ItemType.CUSTOM: 7,
        }
        self.stacked.setCurrentIndex(type_index_map.get(item_type, 0))
        self.totp_secret_edit.setVisible(item_type == ItemType.PASSWORD)

    # ---------------- Load item data into form ----------------
    def _load_item(self):
        idx = self.type_combo.findData(self.item.type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        # Populate according to type
        it = self.item
        if it.type == ItemType.PASSWORD:
            self.title_edit.setText(it.title)
            self.url_edit.setText(it.url or "")
            self.username_edit.setText(it.username)
            self.password_edit.setText(it.password)
            self.notes_edit.setText(it.notes)
        elif it.type == ItemType.NOTE:
            self.note_title_edit.setText(it.title)
            self.note_notes_edit.setText(it.notes)
        elif it.type == ItemType.CREDIT_CARD:
            self.cc_title_edit.setText(it.title)
            self.cc_number_edit.setText(it.card_number or "")
            self.cc_holder_edit.setText(it.card_holder or "")
            self.cc_expiry_edit.setText(it.card_expiry or "")
            self.cc_cvv_edit.setText(it.card_cvv or "")
            self.cc_notes_edit.setText(it.notes)
        elif it.type == ItemType.IDENTITY:
            self.id_title_edit.setText(it.title)
            self.id_firstname_edit.setText(it.id_firstname or "")
            self.id_lastname_edit.setText(it.id_lastname or "")
            self.id_email_edit.setText(it.id_email or "")
            self.id_phone_edit.setText(it.id_phone or "")
            self.id_address_edit.setText(it.id_address or "")
            self.id_notes_edit.setText(it.notes)
        elif it.type == ItemType.WIFI:
            self.wifi_title_edit.setText(it.title)
            self.wifi_ssid_edit.setText(it.wifi_ssid or "")
            self.wifi_password_edit.setText(it.wifi_password or "")
            self.wifi_security_edit.setText(it.wifi_security or "")
            self.wifi_notes_edit.setText(it.notes)
        elif it.type == ItemType.LICENSE:
            self.lic_title_edit.setText(it.title)
            self.lic_vendor_edit.setText(it.license_vendor or "")
            self.lic_key_edit.setText(it.license_key or "")
            self.lic_notes_edit.setText(it.notes)
        elif it.type == ItemType.CRYPTO_SEED:
            self.crypto_title_edit.setText(it.title)
            self.crypto_wallet_type_edit.setText(it.crypto_wallet_type or "")
            self.crypto_seed_phrase_edit.setText(it.crypto_seed_phrase or "")
            self.crypto_notes_edit.setText(it.notes)
        elif it.type == ItemType.CUSTOM:
            # Template selection
            tmpl_name = it.custom_template_id or ""
            idx_t = self.custom_template_combo.findText(tmpl_name)
            if idx_t >= 0:
                self.custom_template_combo.setCurrentIndex(idx_t)
            # Populate dynamic fields
            # We must do this after the template combo has triggered field creation.
            # We'll load custom fields from it.custom_fields
            self._apply_custom_field_values(it.custom_fields)
            self.custom_notes_edit.setText(it.notes)

    def _apply_custom_field_values(self, values_dict):
        for name, widget in getattr(self, 'custom_fields_widgets', {}).items():
            if isinstance(widget, QLineEdit):
                widget.setText(str(values_dict.get(name, "")))
            # Add other widget types if needed

    # ---------------- Save ----------------
    def _save(self):
        self.item.type = self.type_combo.currentData()
        it = self.item
        it.totp_secret = self.totp_secret_edit.text() or None
        it.modified_at = time.time()

        if it.type == ItemType.PASSWORD:
            it.title = self.title_edit.text()
            it.url = self.url_edit.text() or None
            it.username = self.username_edit.text()
            it.password = self.password_edit.text()
            it.notes = self.notes_edit.toPlainText()
        elif it.type == ItemType.NOTE:
            it.title = self.note_title_edit.text()
            it.notes = self.note_notes_edit.toPlainText()
        elif it.type == ItemType.CREDIT_CARD:
            it.title = self.cc_title_edit.text()
            it.card_number = self.cc_number_edit.text() or None
            it.card_holder = self.cc_holder_edit.text() or None
            it.card_expiry = self.cc_expiry_edit.text() or None
            it.card_cvv = self.cc_cvv_edit.text() or None
            it.notes = self.cc_notes_edit.toPlainText()
        elif it.type == ItemType.IDENTITY:
            it.title = self.id_title_edit.text()
            it.id_firstname = self.id_firstname_edit.text() or None
            it.id_lastname = self.id_lastname_edit.text() or None
            it.id_email = self.id_email_edit.text() or None
            it.id_phone = self.id_phone_edit.text() or None
            it.id_address = self.id_address_edit.toPlainText() or None
            it.notes = self.id_notes_edit.toPlainText()
        elif it.type == ItemType.WIFI:
            it.title = self.wifi_title_edit.text()
            it.wifi_ssid = self.wifi_ssid_edit.text() or None
            it.wifi_password = self.wifi_password_edit.text() or None
            it.wifi_security = self.wifi_security_edit.text() or None
            it.notes = self.wifi_notes_edit.toPlainText()
        elif it.type == ItemType.LICENSE:
            it.title = self.lic_title_edit.text()
            it.license_vendor = self.lic_vendor_edit.text() or None
            it.license_key = self.lic_key_edit.text() or None
            it.notes = self.lic_notes_edit.toPlainText()
        elif it.type == ItemType.CRYPTO_SEED:
            it.title = self.crypto_title_edit.text()
            it.crypto_wallet_type = self.crypto_wallet_type_edit.text() or None
            it.crypto_seed_phrase = self.crypto_seed_phrase_edit.toPlainText() or None
            it.notes = self.crypto_notes_edit.toPlainText()
        elif it.type == ItemType.CUSTOM:
            it.title = "Custom Item"  # user could still set a title? We'll use notes maybe.
            it.custom_template_id = self.custom_template_combo.currentData()["name"] if self.custom_template_combo.currentData() else None
            # Collect custom field values
            custom_fields = {}
            if hasattr(self, 'custom_fields_widgets'):
                for name, widget in self.custom_fields_widgets.items():
                    if isinstance(widget, QLineEdit):
                        custom_fields[name] = widget.text()
            it.custom_fields = custom_fields
            it.notes = self.custom_notes_edit.toPlainText()
        self.accept()

    # ---------------- Helper methods ----------------
    def _generate_password(self):
        dialog = GeneratorDialog(self)
        if dialog.exec() == GeneratorDialog.DialogCode.Accepted:
            self.password_edit.setText(dialog.get_password())

    def _setup_totp(self):
        dialog = TotpSetupDialog(self, current_secret=self.totp_secret_edit.text())
        if dialog.exec() == TotpSetupDialog.DialogCode.Accepted:
            self.totp_secret_edit.setText(dialog.get_secret())

    def get_item(self) -> Item:
        return self.item