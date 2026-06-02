from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QSpinBox,
    QCheckBox, QDialogButtonBox, QLabel, QLineEdit,
    QFileDialog, QPushButton, QHBoxLayout, QTabWidget, QWidget, QComboBox
)
from src.utils.config import Config
from src.ui.themes.theme_manager import get_stylesheet, set_theme, get_theme


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(450)
        self.setStyleSheet("""
            QDialog {
                background: qradialgradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:1 #16213e);
                color: #e0e0e0;
            }
            QLabel { color: #e0e0e0; background: transparent; }
            QLineEdit, QSpinBox {
                background: rgba(255,255,255,0.1);
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
            }
            QCheckBox { color: #e0e0e0; }
            QPushButton {
                background: #0f9bff;
                border: none;
                border-radius: 4px;
                color: white;
                padding: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #0091ea; }
        """)
        self._init_ui()
        self._load_config()

    def _init_ui(self):
        layout = QVBoxLayout()
        tabs = QTabWidget()

        # ---------- General tab ----------
        general_tab = QWidget()
        general_form = QFormLayout()
        self.idle_spin = QSpinBox()
        self.idle_spin.setRange(1, 120)
        self.idle_spin.setSuffix(" minutes")
        general_form.addRow("Auto‑lock after:", self.idle_spin)
        self.lock_on_idle_check = QCheckBox("Enable auto‑lock on idle")
        general_form.addRow(self.lock_on_idle_check)
        self.lock_on_sleep_check = QCheckBox("Lock on system sleep")
        general_form.addRow(self.lock_on_sleep_check)

        # Theme selector in General tab
        general_form.addRow(QLabel("Appearance:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Cyber"])
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        general_form.addRow("Theme:", self.theme_combo)

        general_tab.setLayout(general_form)
        tabs.addTab(general_tab, "General")

        # ---------- Advanced Security tab ----------
        adv_tab = QWidget()
        adv_form = QFormLayout()

        # Duress password
        self.duress_enabled_check = QCheckBox("Enable duress password")
        adv_form.addRow(self.duress_enabled_check)
        self.duress_password_edit = QLineEdit()
        self.duress_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.duress_password_edit.setPlaceholderText("Enter duress password")
        adv_form.addRow("Duress password:", self.duress_password_edit)

        # Decoy vault path
        decoy_layout = QHBoxLayout()
        self.decoy_path_edit = QLineEdit()
        self.decoy_path_edit.setPlaceholderText("Path to decoy vault")
        decoy_layout.addWidget(self.decoy_path_edit)
        browse_decoy_btn = QPushButton("Browse")
        browse_decoy_btn.clicked.connect(self._browse_decoy)
        decoy_layout.addWidget(browse_decoy_btn)
        adv_form.addRow("Decoy vault:", decoy_layout)

        # Screen capture blocking
        self.block_capture_check = QCheckBox("Block screen capture (Windows)")
        adv_form.addRow(self.block_capture_check)

        # Memory locking
        self.lock_memory_check = QCheckBox("Lock sensitive memory")
        adv_form.addRow(self.lock_memory_check)

        # Panic shortcut
        self.panic_shortcut_edit = QLineEdit()
        self.panic_shortcut_edit.setPlaceholderText("e.g., Ctrl+Shift+L")
        adv_form.addRow("Panic shortcut:", self.panic_shortcut_edit)

        adv_tab.setLayout(adv_form)
        tabs.addTab(adv_tab, "Advanced Security")

        layout.addWidget(tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def _browse_decoy(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Decoy Vault", "", "Encrypted Vault (*.enc)"
        )
        if path:
            self.decoy_path_edit.setText(path)

    def _on_theme_changed(self):
        """Preview theme immediately when combo changes."""
        theme = self.theme_combo.currentText().lower()
        set_theme(theme)
        main_win = self.window()
        if hasattr(main_win, 'apply_theme'):
            main_win.apply_theme()

    def _load_config(self):
        self.idle_spin.setValue(Config.get("idle_timeout_minutes", 5))
        self.lock_on_idle_check.setChecked(Config.get("lock_on_idle", True))
        self.lock_on_sleep_check.setChecked(Config.get("lock_on_sleep", True))

        current_theme = get_theme().capitalize()
        idx = self.theme_combo.findText(current_theme)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)

        self.duress_enabled_check.setChecked(Config.get("duress_enabled", False))
        self.duress_password_edit.setText(Config.get("duress_password", ""))
        self.decoy_path_edit.setText(Config.get("decoy_vault_path", ""))
        self.block_capture_check.setChecked(Config.get("block_screen_capture", True))
        self.lock_memory_check.setChecked(Config.get("lock_memory", True))
        self.panic_shortcut_edit.setText(Config.get("panic_shortcut", "Ctrl+Shift+L"))

    def _save(self):
        Config.set("idle_timeout_minutes", self.idle_spin.value())
        Config.set("lock_on_idle", self.lock_on_idle_check.isChecked())
        Config.set("lock_on_sleep", self.lock_on_sleep_check.isChecked())

        theme = self.theme_combo.currentText().lower()
        set_theme(theme)

        Config.set("duress_enabled", self.duress_enabled_check.isChecked())
        Config.set("duress_password", self.duress_password_edit.text())
        Config.set("decoy_vault_path", self.decoy_path_edit.text())
        Config.set("block_screen_capture", self.block_capture_check.isChecked())
        Config.set("lock_memory", self.lock_memory_check.isChecked())
        Config.set("panic_shortcut", self.panic_shortcut_edit.text())

        # Apply theme to entire app
        main_win = self.window()
        if hasattr(main_win, 'apply_theme'):
            main_win.apply_theme()

        self.accept()