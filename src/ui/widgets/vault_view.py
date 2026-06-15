"""
Vault content widget — main page of the dashboard.
"""
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QLabel, QMenu, QMessageBox, QApplication,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QAction
from src.core.vault_manager import VaultManager
from src.models.item import Item, ItemType
from src.ui.dialogs.item_dialog import ItemDialog
from src.ui.dialogs.totp_viewer_dialog import TotpViewerDialog
from src.core.totp import generate_totp
from src.main import MATERIAL_ICONS_FAMILY

ICON_FAMILY = MATERIAL_ICONS_FAMILY if MATERIAL_ICONS_FAMILY else "Segoe UI"

TYPE_ICONS = {
    ItemType.PASSWORD:    "\ue897",
    ItemType.NOTE:        "\ue1fc",
    ItemType.CREDIT_CARD: "\ue870",
    ItemType.IDENTITY:    "\uea67",
    ItemType.WIFI:        "\ue63e",
    ItemType.LICENSE:     "\uef76",
    ItemType.CRYPTO_SEED: "\ue0da",
    ItemType.CUSTOM:      "\ue429",
}
TYPE_LABELS = {
    ItemType.PASSWORD:    "Password",
    ItemType.NOTE:        "Note",
    ItemType.CREDIT_CARD: "Card",
    ItemType.IDENTITY:    "Identity",
    ItemType.WIFI:        "WiFi",
    ItemType.LICENSE:     "License",
    ItemType.CRYPTO_SEED: "Crypto",
    ItemType.CUSTOM:      "Custom",
}
TYPE_COLORS = {
    ItemType.PASSWORD:    "#4f8ef7",
    ItemType.NOTE:        "#8888aa",
    ItemType.CREDIT_CARD: "#f05c5c",
    ItemType.IDENTITY:    "#3ecf8e",
    ItemType.WIFI:        "#45b7d1",
    ItemType.LICENSE:     "#f5a623",
    ItemType.CRYPTO_SEED: "#9b59b6",
    ItemType.CUSTOM:      "#a29bfe",
}

FILTER_CHIPS = [
    ("All",       "all"),
    ("Passwords", "password"),
    ("Cards",     "card"),
    ("Notes",     "note"),
]


class ItemCard(QFrame):
    def __init__(self, item: Item, parent=None):
        super().__init__(parent)
        color = TYPE_COLORS.get(item.type, "#4f8ef7")
        self.setObjectName("ItemCard")
        self.setStyleSheet(f"""
            QFrame#ItemCard {{
                background-color: #13131e;
                border: 1px solid #2c2c42;
                border-radius: 10px;
            }}
            QFrame#ItemCard:hover {{
                border-color: {color};
                background-color: #17172a;
            }}
        """)
        self.setMinimumHeight(60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(12)

        # Icon
        icon = QLabel(TYPE_ICONS.get(item.type, "\ue897"))
        icon_font = QFont()
        icon_font.setFamilies([ICON_FAMILY, "Segoe UI"])
        icon_font.setPointSize(18)
        icon.setFont(icon_font)
        icon.setFixedWidth(26)
        icon.setStyleSheet(f"color: {color}; background: transparent;")
        row.addWidget(icon)

        # Text block
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(item.title or "(untitled)")
        title_lbl.setStyleSheet("color: #dde1f0; font-size: 13px; font-weight: 600; background: transparent;")
        text_col.addWidget(title_lbl)

        sub = item.username or item.url or ""
        if sub:
            sub_lbl = QLabel(sub)
            sub_lbl.setStyleSheet("color: #6666888; font-size: 11px; background: transparent;")
            text_col.addWidget(sub_lbl)

        row.addLayout(text_col, stretch=1)

        # Type badge
        badge = QLabel(TYPE_LABELS.get(item.type, "Item"))
        badge.setStyleSheet(f"""
            color: {color};
            font-size: 10px;
            font-weight: 700;
            background: transparent;
            padding: 2px 8px;
            border: 1px solid {color};
            border-radius: 5px;
        """)
        row.addWidget(badge)

        # Chevron
        chev = QLabel("\ue5cc")
        chev_font = QFont()
        chev_font.setFamilies([ICON_FAMILY, "Segoe UI"])
        chev_font.setPointSize(14)
        chev.setFont(chev_font)
        chev.setStyleSheet("color: #3e3e5a; background: transparent;")
        row.addWidget(chev)


class VaultView(QWidget):
    vault_locked = pyqtSignal()

    def __init__(self, manager: VaultManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._current_filter = "all"
        self.clipboard_timer = QTimer()
        self.clipboard_timer.timeout.connect(self._clear_clipboard)
        self._init_ui()
        self.refresh()

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(0)

        # ── Page title ──
        title_row = QHBoxLayout()
        title_row.setSpacing(0)
        page_title = QLabel("Vault")
        page_title.setStyleSheet("font-size: 22px; font-weight: 700; color: #dde1f0;")
        title_row.addWidget(page_title)
        title_row.addStretch()

        # Add button lives in the title row
        self.add_btn = QPushButton("  Add Item")
        self.add_btn.setProperty("primary", True)
        self.add_btn.setStyle(self.add_btn.style())
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setFixedHeight(36)
        self.add_btn.clicked.connect(self._add_item)
        title_row.addWidget(self.add_btn)

        root.addLayout(title_row)
        root.addSpacing(16)

        # ── Search bar ──
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search items…")
        self.search_bar.setFixedHeight(38)
        self.search_bar.textChanged.connect(self._filter_items)
        root.addWidget(self.search_bar)
        root.addSpacing(12)

        # ── Filter chips + stats ──
        chips_row = QHBoxLayout()
        chips_row.setSpacing(8)

        self._chip_buttons: dict[str, QPushButton] = {}
        for label, key in FILTER_CHIPS:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(key == "all")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(28)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #6666888;
                    border: 1px solid #2c2c42;
                    border-radius: 14px;
                    padding: 0 14px;
                    font-size: 12px;
                }
                QPushButton:hover { color: #dde1f0; border-color: #3e3e5a; }
                QPushButton:checked {
                    background: #4f8ef7;
                    color: #ffffff;
                    border-color: #4f8ef7;
                    font-weight: 600;
                }
            """)
            btn.clicked.connect(lambda _, k=key: self._apply_filter(k))
            chips_row.addWidget(btn)
            self._chip_buttons[key] = btn

        chips_row.addStretch()

        self.stats_label = QLabel("0 items")
        self.stats_label.setStyleSheet("color: #6666888; font-size: 12px;")
        chips_row.addWidget(self.stats_label)

        root.addLayout(chips_row)
        root.addSpacing(12)

        # ── Item list ──
        self.item_list = QListWidget()
        self.item_list.setSpacing(4)
        self.item_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.item_list.customContextMenuRequested.connect(self._show_context_menu)
        self.item_list.itemDoubleClicked.connect(self._on_double_click)
        self.item_list.itemSelectionChanged.connect(self._on_selection_changed)
        root.addWidget(self.item_list, stretch=1)
        root.addSpacing(12)

        # ── Action bar (edit / delete — only visible when item selected) ──
        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        action_row.addStretch()

        self.edit_btn = QPushButton("  Edit")
        self.edit_btn.setFixedHeight(34)
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self._edit_item)
        action_row.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("  Delete")
        self.delete_btn.setProperty("danger", True)
        self.delete_btn.setStyle(self.delete_btn.style())
        self.delete_btn.setFixedHeight(34)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete_item)
        action_row.addWidget(self.delete_btn)

        root.addLayout(action_row)
        root.addSpacing(6)

        # ── Status bar ──
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #6666888; font-size: 11px;")
        root.addWidget(self.status_label)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _apply_filter(self, key: str):
        self._current_filter = key
        for k, btn in self._chip_buttons.items():
            btn.setChecked(k == key)
        self._load_items()

    def refresh(self):
        self._load_items()

    def _load_items(self):
        self.item_list.clear()
        try:
            items = self.manager.get_items()
        except RuntimeError:
            self.stats_label.setText("0 items")
            self.status_label.setText("Vault is locked.")
            return

        filter_map = {
            "password": ItemType.PASSWORD,
            "card":     ItemType.CREDIT_CARD,
            "note":     ItemType.NOTE,
        }
        if self._current_filter in filter_map:
            items = [it for it in items if it.type == filter_map[self._current_filter]]

        search = self.search_bar.text().lower()
        if search:
            items = [it for it in items
                     if search in it.title.lower()
                     or search in (it.username or "").lower()
                     or search in (it.url or "").lower()]

        for item in items:
            card = ItemCard(item)
            li = QListWidgetItem()
            li.setData(Qt.ItemDataRole.UserRole, item.uuid)
            li.setSizeHint(card.sizeHint() + QSize(0, 6))
            self.item_list.addItem(li)
            self.item_list.setItemWidget(li, card)

        count = self.item_list.count()
        self.stats_label.setText(f"{count} item{'s' if count != 1 else ''}")
        self.status_label.setText("")

    def _filter_items(self, _text):
        self._load_items()

    def _on_selection_changed(self):
        has = self.item_list.currentItem() is not None
        self.edit_btn.setEnabled(has)
        self.delete_btn.setEnabled(has)

    def _get_item_from_list_item(self, li: QListWidgetItem):
        uuid = li.data(Qt.ItemDataRole.UserRole)
        return next((it for it in self.manager.get_items() if it.uuid == uuid), None)

    # ── CRUD ──────────────────────────────────────────────────────────────────
    def _add_item(self):
        try:
            dlg = ItemDialog(self)
            if dlg.exec() == ItemDialog.DialogCode.Accepted:
                item = dlg.get_item()
                self.manager.add_item(item)
                self._load_items()
                self._set_status(f"Added: {item.title}", success=True)
        except RuntimeError as e:
            QMessageBox.warning(self, "Vault Locked", str(e))
            self.vault_locked.emit()

    def _edit_item(self):
        li = self.item_list.currentItem()
        if not li:
            return
        try:
            item = self._get_item_from_list_item(li)
            if item:
                dlg = ItemDialog(self, item=item)
                if dlg.exec() == ItemDialog.DialogCode.Accepted:
                    self.manager.update_item(dlg.get_item())
                    self._load_items()
                    self._set_status(f"Updated: {item.title}", success=True)
        except RuntimeError as e:
            QMessageBox.warning(self, "Vault Locked", str(e))
            self.vault_locked.emit()

    def _delete_item(self):
        li = self.item_list.currentItem()
        if not li:
            return
        try:
            item = self._get_item_from_list_item(li)
            if item:
                reply = QMessageBox.question(
                    self, "Delete Item",
                    f"Delete \"{item.title}\"? This cannot be undone.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.manager.delete_item(item.uuid)
                    self._load_items()
                    self._set_status(f"Deleted: {item.title}")
        except RuntimeError as e:
            QMessageBox.warning(self, "Vault Locked", str(e))
            self.vault_locked.emit()

    # ── Double-click: copy primary secret ────────────────────────────────────
    def _on_double_click(self, li: QListWidgetItem):
        item = self._get_item_from_list_item(li)
        if not item:
            return
        data = self._get_sensitive_data(item)
        if data:
            clipboard = QApplication.clipboard()
            old_text = clipboard.text()
            clipboard.setText(data)
            self._old_clipboard = old_text
            self._set_status("Copied to clipboard — clears in 30 s", success=True)
            self.clipboard_timer.start(30_000)
        else:
            self._set_status("No sensitive data to copy.")

    def _get_sensitive_data(self, item: Item) -> str:
        if item.type == ItemType.PASSWORD:    return item.password
        if item.type == ItemType.CREDIT_CARD: return item.card_number or ""
        if item.type == ItemType.WIFI:        return item.wifi_password or ""
        if item.type == ItemType.LICENSE:     return item.license_key or ""
        if item.type == ItemType.CRYPTO_SEED: return item.crypto_seed_phrase or ""
        return ""

    def _clear_clipboard(self):
        clipboard = QApplication.clipboard()
        current = clipboard.text()
        if hasattr(self, '_old_clipboard') and current == self._get_last_copied():
            clipboard.setText(self._old_clipboard)
        else:
            clipboard.clear()
        self.clipboard_timer.stop()
        self._set_status("Clipboard cleared.")

    def _get_last_copied(self) -> str:
        return getattr(self, '_last_copied', "")

    def _copy_field(self, value: str, label: str = "Data"):
        if value:
            clipboard = QApplication.clipboard()
            self._old_clipboard = clipboard.text()
            clipboard.setText(value)
            self._last_copied = value
            if sys.platform.startswith("linux"):
                clipboard.clear(mode=QApplication.clipboard().Mode.Selection)
            self._set_status(f"{label} copied!", success=True)

    # ── Context menu ──────────────────────────────────────────────────────────
    def _show_context_menu(self, pos):
        li = self.item_list.currentItem()
        if not li:
            return
        item = self._get_item_from_list_item(li)
        if not item:
            return

        menu = QMenu(self)

        if item.type == ItemType.PASSWORD and item.username:
            a = QAction("Copy Username", self)
            a.triggered.connect(lambda: self._copy_field(item.username, "Username"))
            menu.addAction(a)

        sensitive = self._get_sensitive_data(item)
        if sensitive:
            a = QAction("Copy Secret", self)
            a.triggered.connect(lambda: self._copy_field(sensitive, "Secret"))
            menu.addAction(a)

        if item.totp_secret and item.type == ItemType.PASSWORD:
            a = QAction("View TOTP", self)
            a.triggered.connect(lambda: self._view_totp(item))
            menu.addAction(a)
            a2 = QAction("Copy TOTP Code", self)
            a2.triggered.connect(lambda: self._copy_totp(item))
            menu.addAction(a2)

        menu.addSeparator()
        ea = QAction("Edit", self)
        ea.triggered.connect(self._edit_item)
        menu.addAction(ea)
        da = QAction("Delete", self)
        da.triggered.connect(self._delete_item)
        menu.addAction(da)

        menu.exec(self.item_list.mapToGlobal(pos))

    def _copy_field(self, value: str, label: str = "Data"):
        if value:
            QApplication.clipboard().setText(value)
            self._set_status(f"{label} copied!", success=True)

    def _view_totp(self, item: Item):
        TotpViewerDialog(item.totp_secret, item.title, self).exec()

    def _copy_totp(self, item: Item):
        try:
            clipboard = QApplication.clipboard()
            self._old_clipboard = clipboard.text()
            clipboard.setText(generate_totp(item.totp_secret))
            self._last_copied = generate_totp(item.totp_secret)
            self._set_status("TOTP code copied!", success=True)
        except Exception as e:
            QMessageBox.critical(self, "TOTP Error", str(e))

    def _set_status(self, msg: str, success: bool = False):
        color = "#3ecf8e" if success else "#6666888"
        self.status_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        self.status_label.setText(msg)
