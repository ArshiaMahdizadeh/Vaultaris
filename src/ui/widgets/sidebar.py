from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSpacerItem, QSizePolicy, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QFont
from src.main import MATERIAL_ICONS_FAMILY

ICON_FAMILY = MATERIAL_ICONS_FAMILY if MATERIAL_ICONS_FAMILY else "Segoe UI"

# Material Icons codepoints
ICONS = {
    "vault":    "\ue2c8",   # folder_open
    "gen":      "\ue0da",   # vpn_key
    "totp":     "\ue425",   # timer
    "audit":    "\ue32a",   # security
    "io":       "\ue0d3",   # import_export
    "settings": "\ue8b8",   # settings
    "lock":     "\ue899",   # lock_outline
    "logo":     "\ue9e8",   # shield
}

NAV_ITEMS = [
    ("vault",    "Vault",            0),
    ("gen",      "Generator",        1),
    ("totp",     "Authenticator",    2),
    ("audit",    "Audit",            3),
    ("io",       "Import / Export",  4),
    ("settings", "Settings",         5),
]

# Per-theme colours — kept here so the sidebar never needs a full stylesheet swap
_THEMES = {
    "dark": {
        "bg":           "#0a0a14",
        "border":       "#1a1a28",
        "text_idle":    "#666688",
        "text_hover":   "#dde1f0",
        "text_active":  "#ffffff",
        "hover_bg":     "#14142a",
        "active_bg":    "#1a1a30",
        "accent":       "#4f8ef7",
        "logo_text":    "#dde1f0",
        "logo_icon":    "#4f8ef7",
    },
    "light": {
        "bg":           "#ffffff",
        "border":       "#e5e5ea",
        "text_idle":    "#8e8e93",
        "text_hover":   "#1c1c1e",
        "text_active":  "#1c1c1e",
        "hover_bg":     "#f2f2f7",
        "active_bg":    "#e8e8ed",
        "accent":       "#007aff",
        "logo_text":    "#1c1c1e",
        "logo_icon":    "#007aff",
    },
    "cyber": {
        "bg":           "#08081a",
        "border":       "#1e3040",
        "text_idle":    "#2a4a60",
        "text_hover":   "#00d4ff",
        "text_active":  "#ff2d78",
        "hover_bg":     "#0f0f28",
        "active_bg":    "#1a1a3a",
        "accent":       "#ff2d78",
        "logo_text":    "#b0e8ff",
        "logo_icon":    "#00d4ff",
    },
}


def _icon_font(size: int = 20) -> QFont:
    f = QFont()
    f.setFamilies([ICON_FAMILY, "Segoe UI"])
    f.setPointSize(size)
    return f


def _text_font(size: int = 13, bold: bool = False) -> QFont:
    f = QFont("Segoe UI", size)
    if bold:
        f.setWeight(QFont.Weight.DemiBold)
    return f


class NavButton(QWidget):
    """
    A sidebar nav item built from two QLabels (icon + text) so the icon font
    and the label font are completely independent — no bleed-through.
    """
    clicked = pyqtSignal()

    def __init__(self, icon_key: str, label: str, parent=None):
        super().__init__(parent)
        self._checked = False
        self._theme = "dark"

        self.setFixedHeight(46)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        row = QHBoxLayout(self)
        row.setContentsMargins(20, 0, 16, 0)
        row.setSpacing(12)

        self._icon_lbl = QLabel(ICONS.get(icon_key, ""))
        self._icon_lbl.setFont(_icon_font(18))
        self._icon_lbl.setFixedWidth(22)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self._icon_lbl)

        self._text_lbl = QLabel(label)
        self._text_lbl.setFont(_text_font(13))
        row.addWidget(self._text_lbl, stretch=1)

        # Left-accent bar (hidden when not active)
        self._accent = QFrame(self)
        self._accent.setFixedWidth(3)
        self._accent.hide()

        self._apply_colors()

    # ── State ─────────────────────────────────────────────────────────────────
    def set_checked(self, checked: bool):
        self._checked = checked
        self._apply_colors()

    def is_checked(self) -> bool:
        return self._checked

    def apply_theme(self, theme: str):
        self._theme = theme
        self._apply_colors()

    def _apply_colors(self):
        t = _THEMES.get(self._theme, _THEMES["dark"])
        if self._checked:
            bg     = t["active_bg"]
            icon_c = t["accent"]
            text_c = t["text_active"]
            self._accent.show()
            self._accent.setStyleSheet(f"background: {t['accent']}; border: none;")
            self._accent.setGeometry(0, 0, 3, self.height())
            # Indent text to compensate for the 3px accent bar
            self.layout().setContentsMargins(17, 0, 16, 0)
        else:
            bg     = "transparent"
            icon_c = t["text_idle"]
            text_c = t["text_idle"]
            self._accent.hide()
            self.layout().setContentsMargins(20, 0, 16, 0)

        self.setStyleSheet(f"QWidget {{ background: {bg}; }}")
        self._icon_lbl.setStyleSheet(f"color: {icon_c}; background: transparent;")
        self._text_lbl.setStyleSheet(f"color: {text_c}; background: transparent;")

    # ── Hover ─────────────────────────────────────────────────────────────────
    def enterEvent(self, event):
        if not self._checked:
            t = _THEMES.get(self._theme, _THEMES["dark"])
            self.setStyleSheet(f"QWidget {{ background: {t['hover_bg']}; }}")
            self._icon_lbl.setStyleSheet(f"color: {t['text_hover']}; background: transparent;")
            self._text_lbl.setStyleSheet(f"color: {t['text_hover']}; background: transparent;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_colors()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def resizeEvent(self, event):
        if self._checked:
            self._accent.setGeometry(0, 0, 3, self.height())
        super().resizeEvent(event)


class Sidebar(QWidget):
    page_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = "dark"
        self.setFixedWidth(220)
        self._apply_bg()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Logo row ──
        logo_row = QWidget()
        logo_row.setFixedHeight(64)
        logo_inner = QHBoxLayout(logo_row)
        logo_inner.setContentsMargins(20, 0, 16, 0)
        logo_inner.setSpacing(10)

        self._logo_icon = QLabel(ICONS["logo"])
        self._logo_icon.setFont(_icon_font(20))
        self._logo_icon.setFixedWidth(24)
        logo_inner.addWidget(self._logo_icon)

        self._logo_text = QLabel("Vaultaris")
        self._logo_text.setFont(_text_font(15, bold=True))
        logo_inner.addWidget(self._logo_text, stretch=1)

        root.addWidget(logo_row)

        # ── Divider ──
        div = QFrame()
        div.setFixedHeight(1)
        div.setObjectName("SidebarDivider")
        root.addWidget(div)
        self._divider = div

        root.addSpacing(4)

        # ── Nav buttons ──
        self._nav_buttons: dict[int, NavButton] = {}
        for key, label, idx in NAV_ITEMS:
            btn = NavButton(key, label)
            btn.clicked.connect(self._on_nav_clicked)
            btn.setProperty("page_index", idx)
            root.addWidget(btn)
            self._nav_buttons[idx] = btn

        root.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # ── Divider ──
        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setObjectName("SidebarDivider")
        root.addWidget(div2)
        self._divider2 = div2

        # ── Lock button ──
        self.lock_btn = NavButton("lock", "Lock Vault")
        self.lock_btn.clicked.connect(self._on_lock_clicked)
        root.addWidget(self.lock_btn)
        root.addSpacing(8)

        # Default selection
        self._nav_buttons[0].set_checked(True)
        self._update_logo_colors()
        self._update_dividers()

    # ── Theme ─────────────────────────────────────────────────────────────────
    def apply_theme(self, theme: str):
        self._theme = theme
        self._apply_bg()
        self._update_logo_colors()
        self._update_dividers()
        for btn in self._nav_buttons.values():
            btn.apply_theme(theme)
        self.lock_btn.apply_theme(theme)

    def _apply_bg(self):
        t = _THEMES.get(self._theme, _THEMES["dark"])
        self.setStyleSheet(
            f"Sidebar {{ background-color: {t['bg']}; "
            f"border-right: 1px solid {t['border']}; }}"
        )

    def _update_logo_colors(self):
        t = _THEMES.get(self._theme, _THEMES["dark"])
        self._logo_icon.setStyleSheet(f"color: {t['logo_icon']}; background: transparent;")
        self._logo_text.setStyleSheet(f"color: {t['logo_text']}; background: transparent;")

    def _update_dividers(self):
        t = _THEMES.get(self._theme, _THEMES["dark"])
        style = f"background: {t['border']}; border: none;"
        self._divider.setStyleSheet(style)
        self._divider2.setStyleSheet(style)

    # ── Navigation ────────────────────────────────────────────────────────────
    def _clear_checks(self):
        for btn in self._nav_buttons.values():
            btn.set_checked(False)
        self.lock_btn.set_checked(False)

    def _on_nav_clicked(self):
        sender = self.sender()
        if not isinstance(sender, NavButton):
            return
        self._clear_checks()
        sender.set_checked(True)
        idx = sender.property("page_index")
        if idx is not None:
            self.page_changed.emit(idx)

    def _on_lock_clicked(self):
        self._clear_checks()
        self.lock_btn.set_checked(True)
        self.window().lock_vault()

    def set_active_page(self, index: int):
        self._clear_checks()
        if index in self._nav_buttons:
            self._nav_buttons[index].set_checked(True)
