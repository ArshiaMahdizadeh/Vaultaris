from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QDialog, QApplication
)
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import QTimer
from src.core.vault_manager import VaultManager
from src.ui.dialogs.unlock_dialog import UnlockDialog
from src.ui.widgets.vault_view import VaultView
from src.ui.widgets.generator_widget import GeneratorWidget
from src.ui.widgets.totp_widget import TotpWidget
from src.ui.widgets.audit_widget import AuditWidget
from src.ui.widgets.import_export_widget import ImportExportWidget
from src.ui.widgets.settings_widget import SettingsWidget
from src.ui.widgets.sidebar import Sidebar
from src.ui.widgets.animated_stack import AnimatedStack
from src.core.idle_detector import IdleDetector
from src.utils.config import Config
from src.core.security_utils import lock_memory, disable_core_dumps, set_screen_capture_blocking
from src.ui.themes.theme_manager import get_stylesheet, get_theme


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vaultaris")
        self.resize(1100, 700)
        self.setMinimumSize(900, 600)

        if Config.get("lock_memory", True):
            lock_memory()
        disable_core_dumps()

        if Config.get("block_screen_capture", True):
            set_screen_capture_blocking(int(self.winId()), True)

        self.manager = VaultManager()
        self.idle_detector = IdleDetector(self)
        self.idle_detector.idle_timeout.connect(self._on_idle_timeout)
        self.idle_detector.sleep_detected.connect(self._on_sleep)
        self.panic_shortcut = None
        self.sidebar = None

        self._show_unlock()

    # ── Unlock / lock flow ────────────────────────────────────────────────────
    def _show_unlock(self):
        self.idle_detector.stop()
        set_screen_capture_blocking(int(self.winId()), False)
        if self.panic_shortcut:
            self.panic_shortcut.deleteLater()
            self.panic_shortcut = None

        dialog = UnlockDialog(self.manager, parent=None)
        if Config.get("block_screen_capture", True):
            set_screen_capture_blocking(int(dialog.winId()), True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._build_ui()
            self._show_vault()
        else:
            self.close()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(parent=self)
        self.sidebar.page_changed.connect(self._switch_page)

        # Animated content area
        self.content_stack = AnimatedStack(duration=200)

        # Pages
        self.vault_page     = VaultView(self.manager)
        self.vault_page.vault_locked.connect(self._on_vault_locked)
        self.generator_page = GeneratorWidget()
        self.totp_page      = TotpWidget(self.manager)
        self.audit_page     = AuditWidget(self.manager)
        self.io_page        = ImportExportWidget(self.manager)
        self.settings_page  = SettingsWidget()

        self.content_stack.addWidget(self.vault_page)       # 0
        self.content_stack.addWidget(self.generator_page)   # 1
        self.content_stack.addWidget(self.totp_page)        # 2
        self.content_stack.addWidget(self.audit_page)       # 3
        self.content_stack.addWidget(self.io_page)          # 4
        self.content_stack.addWidget(self.settings_page)    # 5

        layout.addWidget(self.sidebar)
        layout.addWidget(self.content_stack, stretch=1)

        self.apply_theme()

        if Config.get("block_screen_capture", True):
            set_screen_capture_blocking(int(self.winId()), True)

        shortcut_str = Config.get("panic_shortcut", "Ctrl+Shift+L")
        self.panic_shortcut = QShortcut(QKeySequence(shortcut_str), self)
        self.panic_shortcut.activated.connect(self._panic_action)

    # ── Theme ─────────────────────────────────────────────────────────────────
    def apply_theme(self):
        """
        Apply the global QSS to the app, then tell the sidebar to repaint
        itself using its own colour table — no stylesheet replacement on the
        sidebar widget, so its layout never collapses.
        """
        theme = get_theme()
        QApplication.instance().setStyleSheet(get_stylesheet(theme))
        if self.sidebar:
            self.sidebar.apply_theme(theme)

    # ── Navigation ────────────────────────────────────────────────────────────
    def _switch_page(self, index: int):
        self.content_stack.setCurrentIndex(index)
        # Refresh data-driven pages on arrival
        if index == 0:
            self.vault_page.refresh()
        elif index == 2:
            self.totp_page._populate_list()
        elif index == 3:
            self.audit_page._run_analysis()

    # ── Vault lifecycle ───────────────────────────────────────────────────────
    def _show_vault(self):
        self.vault_page.refresh()
        self.show()
        self.raise_()
        self.activateWindow()
        self.idle_detector.reset()
        self._start_idle_detector()

    def _start_idle_detector(self):
        try:
            minutes = Config.get("idle_timeout_minutes", 5)
            if minutes < 2:
                minutes = 5
                Config.set("idle_timeout_minutes", 5)
            self.idle_detector.set_timeout_minutes(minutes)
            self.idle_detector.start()
        except Exception:
            pass

    def lock_vault(self):
        if self.manager.active_vault:
            self.manager.lock_active_vault()
            self._on_vault_locked()

    def _on_vault_locked(self):
        self.idle_detector.stop()
        set_screen_capture_blocking(int(self.winId()), False)
        if self.panic_shortcut:
            self.panic_shortcut.deleteLater()
            self.panic_shortcut = None
        self.hide()
        self._show_unlock()

    def _on_idle_timeout(self):
        if self.manager.active_vault:
            self.manager.lock_active_vault()
            self._on_vault_locked()

    def _on_sleep(self):
        if Config.get("lock_on_sleep", True):
            if self.manager.active_vault:
                self.manager.lock_active_vault()
                self._on_vault_locked()

    def _panic_action(self):
        if self.manager.active_vault:
            self.manager.lock_active_vault()
            self._on_vault_locked()
