from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QSpinBox,
    QCheckBox, QLabel, QLineEdit, QPushButton, QFileDialog,
    QComboBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt
from src.utils.config import Config
from src.ui.themes.theme_manager import set_theme, get_theme


def _section(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color: #8888aa; font-size: 11px; font-weight: 600; "
        "letter-spacing: 1px; padding-top: 8px;"
    )
    return lbl


class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_config()

    def _init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(0)

        # ── Page title + save button ──
        hdr = QHBoxLayout()
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #dde1f0;")
        hdr.addWidget(title)
        hdr.addStretch()
        save_btn = QPushButton("Save")
        save_btn.setProperty("primary", True)
        save_btn.setStyle(save_btn.style())
        save_btn.setFixedHeight(36)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save)
        hdr.addWidget(save_btn)
        root.addLayout(hdr)
        root.addSpacing(20)

        # ── General ──
        root.addWidget(_section("GENERAL"))
        root.addSpacing(8)

        gen_form = QFormLayout()
        gen_form.setSpacing(10)
        gen_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.idle_spin = QSpinBox()
        self.idle_spin.setRange(2, 120)
        self.idle_spin.setSuffix(" min")
        self.idle_spin.setFixedWidth(100)
        gen_form.addRow("Auto-lock after:", self.idle_spin)

        self.lock_on_idle = QCheckBox("Lock on idle")
        gen_form.addRow("", self.lock_on_idle)

        self.lock_on_sleep = QCheckBox("Lock on system sleep")
        gen_form.addRow("", self.lock_on_sleep)

        root.addLayout(gen_form)
        root.addSpacing(16)

        # ── Appearance ──
        root.addWidget(_section("APPEARANCE"))
        root.addSpacing(8)

        theme_row = QHBoxLayout()
        theme_row.setSpacing(8)
        theme_lbl = QLabel("Theme:")
        theme_lbl.setStyleSheet("color: #dde1f0;")
        theme_row.addWidget(theme_lbl)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Cyber"])
        self.theme_combo.setFixedWidth(160)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch()
        root.addLayout(theme_row)
        root.addSpacing(16)

        # ── Advanced Security ──
        root.addWidget(_section("ADVANCED SECURITY"))
        root.addSpacing(8)

        sec_form = QFormLayout()
        sec_form.setSpacing(10)
        sec_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.duress_enabled = QCheckBox("Enable duress password")
        sec_form.addRow("", self.duress_enabled)

        self.duress_password = QLineEdit()
        self.duress_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.duress_password.setPlaceholderText("Duress password")
        sec_form.addRow("Duress password:", self.duress_password)

        decoy_row = QHBoxLayout()
        decoy_row.setSpacing(8)
        self.decoy_path = QLineEdit()
        self.decoy_path.setPlaceholderText("Path to decoy vault (.enc)")
        decoy_row.addWidget(self.decoy_path, stretch=1)
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedHeight(34)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_decoy)
        decoy_row.addWidget(browse_btn)
        sec_form.addRow("Decoy vault:", decoy_row)

        self.block_capture = QCheckBox("Block screen capture (Windows 10 2004+)")
        sec_form.addRow("", self.block_capture)

        self.lock_memory = QCheckBox("Lock memory (best effort)")
        sec_form.addRow("", self.lock_memory)

        self.panic_shortcut = QLineEdit()
        self.panic_shortcut.setPlaceholderText("e.g. Ctrl+Shift+L")
        self.panic_shortcut.setFixedWidth(180)
        sec_form.addRow("Panic shortcut:", self.panic_shortcut)

        root.addLayout(sec_form)
        root.addStretch()

        scroll.setWidget(inner)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _browse_decoy(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Decoy Vault", "", "Encrypted Vault (*.enc)"
        )
        if path:
            self.decoy_path.setText(path)

    def _on_theme_changed(self):
        theme = self.theme_combo.currentText().lower()
        set_theme(theme)
        main_win = self.window()
        if hasattr(main_win, "apply_theme"):
            main_win.apply_theme()

    def _load_config(self):
        self.idle_spin.setValue(Config.get("idle_timeout_minutes", 5))
        self.lock_on_idle.setChecked(Config.get("lock_on_idle", True))
        self.lock_on_sleep.setChecked(Config.get("lock_on_sleep", True))

        theme = get_theme().capitalize()
        idx = self.theme_combo.findText(theme)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)

        self.duress_enabled.setChecked(Config.get("duress_enabled", False))
        self.duress_password.setText(Config.get("duress_password", ""))
        self.decoy_path.setText(Config.get("decoy_vault_path", ""))
        self.block_capture.setChecked(Config.get("block_screen_capture", True))
        self.lock_memory.setChecked(Config.get("lock_memory", True))
        self.panic_shortcut.setText(Config.get("panic_shortcut", "Ctrl+Shift+L"))

    def _save(self):
        Config.set("idle_timeout_minutes", self.idle_spin.value())
        Config.set("lock_on_idle", self.lock_on_idle.isChecked())
        Config.set("lock_on_sleep", self.lock_on_sleep.isChecked())

        theme = self.theme_combo.currentText().lower()
        set_theme(theme)

        Config.set("duress_enabled", self.duress_enabled.isChecked())
        Config.set("duress_password", self.duress_password.text())
        Config.set("decoy_vault_path", self.decoy_path.text())
        Config.set("block_screen_capture", self.block_capture.isChecked())
        Config.set("lock_memory", self.lock_memory.isChecked())
        Config.set("panic_shortcut", self.panic_shortcut.text())

        main_win = self.window()
        if hasattr(main_win, "apply_theme"):
            main_win.apply_theme()
        if hasattr(main_win, "idle_detector"):
            main_win.idle_detector.set_timeout_minutes(self.idle_spin.value())
