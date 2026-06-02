"""
Central theme manager. Returns QSS stylesheets for dark / light / cyber themes.
"""
from src.utils.config import Config

# ── Shared design tokens ──────────────────────────────────────────────────────
ACCENT   = "#4f8ef7"   # primary blue
ACCENT_H = "#6aa3ff"   # hover
ACCENT_P = "#3a7be0"   # pressed
DANGER   = "#f05c5c"
SUCCESS  = "#3ecf8e"
WARNING  = "#f5a623"


def get_theme() -> str:
    return Config.get("theme", "dark")


def set_theme(theme_name: str):
    Config.set("theme", theme_name)


def get_stylesheet(theme_name: str = None) -> str:
    if theme_name is None:
        theme_name = get_theme()
    if theme_name == "light":
        return LIGHT_STYLESHEET
    if theme_name == "cyber":
        return CYBER_STYLESHEET
    return DARK_STYLESHEET


def get_sidebar_style(theme_name: str = None) -> str:
    if theme_name is None:
        theme_name = get_theme()
    if theme_name == "light":
        return LIGHT_SIDEBAR_STYLE
    if theme_name == "cyber":
        return CYBER_SIDEBAR_STYLE
    return DARK_SIDEBAR_STYLE


# ── Dark Theme ────────────────────────────────────────────────────────────────
DARK_STYLESHEET = """
* {
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
    outline: none;
}
QMainWindow, QDialog {
    background-color: #0e0e16;
}
QWidget {
    background-color: #0e0e16;
    color: #dde1f0;
}
/* ── Buttons ── */
QPushButton {
    background-color: #1a1a28;
    border: 1px solid #2c2c42;
    border-radius: 8px;
    padding: 9px 18px;
    color: #dde1f0;
    font-weight: 500;
    min-height: 20px;
}
QPushButton:hover  { background-color: #252538; border-color: #3e3e5a; }
QPushButton:pressed{ background-color: #2e2e48; }
QPushButton:disabled{ background-color: #13131e; color: #44445a; border-color: #1a1a28; }
QPushButton[primary="true"] {
    background-color: #4f8ef7;
    border: none;
    color: #ffffff;
    font-weight: 600;
}
QPushButton[primary="true"]:hover  { background-color: #6aa3ff; }
QPushButton[primary="true"]:pressed{ background-color: #3a7be0; }
QPushButton[danger="true"] {
    background-color: transparent;
    border: 1px solid #2c2c42;
    color: #f05c5c;
}
QPushButton[danger="true"]:hover  { background-color: #2a1a1a; border-color: #f05c5c; }
QPushButton[danger="true"]:pressed{ background-color: #3a1a1a; }
QPushButton[danger="true"]:disabled{ color: #44445a; border-color: #1a1a28; }
/* ── Inputs ── */
QLineEdit, QTextEdit, QSpinBox {
    background-color: #13131e;
    border: 1px solid #2c2c42;
    border-radius: 8px;
    padding: 9px 12px;
    color: #dde1f0;
    selection-background-color: #4f8ef7;
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus { border-color: #4f8ef7; }
QSpinBox::up-button, QSpinBox::down-button {
    background: #1a1a28; border: 1px solid #2c2c42; width: 18px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: #252538; }
/* ── ComboBox ── */
QComboBox {
    background-color: #13131e;
    border: 1px solid #2c2c42;
    border-radius: 8px;
    padding: 9px 12px;
    color: #dde1f0;
}
QComboBox:focus { border-color: #4f8ef7; }
QComboBox::drop-down { border-left: 1px solid #2c2c42; width: 26px; }
QComboBox QAbstractItemView {
    background-color: #13131e;
    border: 1px solid #2c2c42;
    color: #dde1f0;
    selection-background-color: #4f8ef7;
    selection-color: #ffffff;
}
/* ── Lists ── */
QListWidget {
    background-color: transparent;
    border: none;
    color: #dde1f0;
    outline: none;
}
QListWidget::item { padding: 0; border: none; background: transparent; }
QListWidget::item:selected { background: transparent; }
QScrollBar:vertical {
    background: #0e0e16; width: 6px; border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #2c2c42; border-radius: 3px; min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #3e3e5a; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
/* ── Labels ── */
QLabel { background: transparent; color: #dde1f0; }
/* ── Progress ── */
QProgressBar {
    border: 1px solid #2c2c42; border-radius: 6px;
    text-align: center; color: #dde1f0; background-color: #13131e;
    min-height: 10px;
}
QProgressBar::chunk { background-color: #4f8ef7; border-radius: 4px; }
/* ── Checkboxes ── */
QCheckBox { color: #dde1f0; spacing: 8px; }
QCheckBox::indicator {
    width: 17px; height: 17px;
    border: 1px solid #3e3e5a; border-radius: 4px;
    background-color: #13131e;
}
QCheckBox::indicator:checked { background-color: #4f8ef7; border-color: #4f8ef7; }
QCheckBox::indicator:hover   { border-color: #4f8ef7; }
/* ── GroupBox ── */
QGroupBox {
    border: 1px solid #2c2c42; border-radius: 10px;
    margin-top: 18px; padding-top: 14px;
    color: #8888aa; font-weight: 600; font-size: 11px;
    text-transform: uppercase; letter-spacing: 1px;
}
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
/* ── Tabs ── */
QTabWidget::pane { border: 1px solid #2c2c42; border-radius: 8px; }
QTabBar::tab {
    background-color: #13131e; border: 1px solid #2c2c42;
    border-bottom: none; border-radius: 8px 8px 0 0;
    padding: 9px 18px; color: #8888aa;
}
QTabBar::tab:selected { background-color: #1a1a28; color: #dde1f0; }
QTabBar::tab:hover    { background-color: #1a1a28; color: #dde1f0; }
/* ── Menu ── */
QMenu {
    background: #1a1a28; color: #dde1f0;
    border: 1px solid #2c2c42; border-radius: 8px; padding: 6px;
}
QMenu::item { padding: 8px 20px; border-radius: 6px; }
QMenu::item:selected { background: #4f8ef7; color: #ffffff; }
QMenu::separator { background: #2c2c42; height: 1px; margin: 4px 0; }
/* ── MessageBox ── */
QMessageBox { background-color: #0e0e16; }
QMessageBox QLabel { color: #dde1f0; }
"""

# ── Light Theme ───────────────────────────────────────────────────────────────
LIGHT_STYLESHEET = """
* { font-family: "Segoe UI", sans-serif; font-size: 13px; outline: none; }
QMainWindow, QDialog { background-color: #f2f2f7; }
QWidget { background-color: #f2f2f7; color: #1c1c1e; }
QPushButton {
    background-color: #ffffff; border: 1px solid #d1d1d6;
    border-radius: 8px; padding: 9px 18px; color: #1c1c1e; font-weight: 500;
}
QPushButton:hover  { background-color: #e8e8ed; border-color: #aeaeb2; }
QPushButton:pressed{ background-color: #d1d1d6; }
QPushButton:disabled{ background-color: #e8e8ed; color: #8e8e93; }
QPushButton[primary="true"] {
    background-color: #007aff; border: none; color: #ffffff; font-weight: 600;
}
QPushButton[primary="true"]:hover  { background-color: #3395ff; }
QPushButton[primary="true"]:pressed{ background-color: #0062cc; }
QPushButton[danger="true"] {
    background-color: transparent; border: 1px solid #d1d1d6; color: #ff3b30;
}
QPushButton[danger="true"]:hover  { background-color: #fff0ef; border-color: #ff3b30; }
QPushButton[danger="true"]:disabled{ color: #8e8e93; border-color: #d1d1d6; }
QLineEdit, QTextEdit, QSpinBox {
    background-color: #ffffff; border: 1px solid #d1d1d6;
    border-radius: 8px; padding: 9px 12px; color: #1c1c1e;
    selection-background-color: #007aff;
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus { border-color: #007aff; }
QSpinBox::up-button, QSpinBox::down-button {
    background: #f2f2f7; border: 1px solid #d1d1d6; width: 18px;
}
QComboBox {
    background-color: #ffffff; border: 1px solid #d1d1d6;
    border-radius: 8px; padding: 9px 12px; color: #1c1c1e;
}
QComboBox:focus { border-color: #007aff; }
QComboBox::drop-down { border-left: 1px solid #d1d1d6; width: 26px; }
QComboBox QAbstractItemView {
    background-color: #ffffff; border: 1px solid #d1d1d6;
    color: #1c1c1e; selection-background-color: #007aff; selection-color: #ffffff;
}
QListWidget { background-color: transparent; border: none; outline: none; }
QListWidget::item { padding: 0; border: none; background: transparent; }
QListWidget::item:selected { background: transparent; }
QScrollBar:vertical { background: #f2f2f7; width: 6px; border-radius: 3px; }
QScrollBar::handle:vertical { background: #c7c7cc; border-radius: 3px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #aeaeb2; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QLabel { background: transparent; color: #1c1c1e; }
QProgressBar {
    border: 1px solid #d1d1d6; border-radius: 6px;
    text-align: center; color: #1c1c1e; background-color: #ffffff; min-height: 10px;
}
QProgressBar::chunk { background-color: #007aff; border-radius: 4px; }
QCheckBox { color: #1c1c1e; spacing: 8px; }
QCheckBox::indicator {
    width: 17px; height: 17px; border: 1px solid #aeaeb2;
    border-radius: 4px; background-color: #ffffff;
}
QCheckBox::indicator:checked { background-color: #007aff; border-color: #007aff; }
QGroupBox {
    border: 1px solid #d1d1d6; border-radius: 10px;
    margin-top: 18px; padding-top: 14px;
    color: #8e8e93; font-weight: 600; font-size: 11px;
}
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
QTabWidget::pane { border: 1px solid #d1d1d6; border-radius: 8px; }
QTabBar::tab {
    background-color: #ffffff; border: 1px solid #d1d1d6;
    border-bottom: none; border-radius: 8px 8px 0 0;
    padding: 9px 18px; color: #8e8e93;
}
QTabBar::tab:selected { background-color: #f2f2f7; color: #1c1c1e; }
QTabBar::tab:hover    { background-color: #e8e8ed; color: #1c1c1e; }
QMenu {
    background: #ffffff; color: #1c1c1e;
    border: 1px solid #d1d1d6; border-radius: 8px; padding: 6px;
}
QMenu::item { padding: 8px 20px; border-radius: 6px; }
QMenu::item:selected { background: #007aff; color: #ffffff; }
QMenu::separator { background: #d1d1d6; height: 1px; margin: 4px 0; }
QMessageBox { background-color: #f2f2f7; }
QMessageBox QLabel { color: #1c1c1e; }
"""

# ── Cyber Theme ───────────────────────────────────────────────────────────────
CYBER_STYLESHEET = """
* { font-family: "Segoe UI", sans-serif; font-size: 13px; outline: none; }
QMainWindow, QDialog { background-color: #060612; }
QWidget { background-color: #060612; color: #b0e8ff; }
QPushButton {
    background-color: #0a0a20; border: 1px solid #00d4ff;
    border-radius: 8px; padding: 9px 18px; color: #00d4ff; font-weight: 500;
}
QPushButton:hover  { background-color: #00d4ff; color: #060612; }
QPushButton:pressed{ background-color: #00a8cc; color: #060612; }
QPushButton:disabled{ background-color: #0a0a20; color: #1e3040; border-color: #1e3040; }
QPushButton[primary="true"] {
    background-color: #00d4ff; border: none; color: #060612; font-weight: 700;
}
QPushButton[primary="true"]:hover  { background-color: #33ddff; }
QPushButton[primary="true"]:pressed{ background-color: #00a8cc; }
QPushButton[danger="true"] {
    background-color: transparent; border: 1px solid #00d4ff; color: #ff2d78;
}
QPushButton[danger="true"]:hover  { background-color: #1a0010; border-color: #ff2d78; }
QPushButton[danger="true"]:disabled{ color: #1e3040; border-color: #1e3040; }
QLineEdit, QTextEdit, QSpinBox {
    background-color: #0a0a20; border: 1px solid #1e3040;
    border-radius: 8px; padding: 9px 12px; color: #b0e8ff;
    selection-background-color: #ff2d78;
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus { border-color: #ff2d78; }
QSpinBox::up-button, QSpinBox::down-button {
    background: #0a0a20; border: 1px solid #1e3040; width: 18px;
}
QComboBox {
    background-color: #0a0a20; border: 1px solid #1e3040;
    border-radius: 8px; padding: 9px 12px; color: #00d4ff;
}
QComboBox:focus { border-color: #ff2d78; }
QComboBox::drop-down { border-left: 1px solid #1e3040; width: 26px; }
QComboBox QAbstractItemView {
    background-color: #0a0a20; border: 1px solid #1e3040;
    color: #b0e8ff; selection-background-color: #1a1a3a; selection-color: #ff2d78;
}
QListWidget { background-color: transparent; border: none; outline: none; }
QListWidget::item { padding: 0; border: none; background: transparent; }
QListWidget::item:selected { background: transparent; }
QScrollBar:vertical { background: #060612; width: 6px; border-radius: 3px; }
QScrollBar::handle:vertical { background: #1e3040; border-radius: 3px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #00d4ff; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QLabel { background: transparent; color: #b0e8ff; }
QProgressBar {
    border: 1px solid #1e3040; border-radius: 6px;
    text-align: center; color: #00d4ff; background-color: #0a0a20; min-height: 10px;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #ff2d78,stop:1 #00d4ff);
    border-radius: 4px;
}
QCheckBox { color: #b0e8ff; spacing: 8px; }
QCheckBox::indicator {
    width: 17px; height: 17px; border: 1px solid #00d4ff;
    border-radius: 4px; background-color: #0a0a20;
}
QCheckBox::indicator:checked { background-color: #00d4ff; border-color: #00d4ff; }
QGroupBox {
    border: 1px solid #1e3040; border-radius: 10px;
    margin-top: 18px; padding-top: 14px;
    color: #ff2d78; font-weight: 600; font-size: 11px;
}
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
QTabWidget::pane { border: 1px solid #1e3040; border-radius: 8px; }
QTabBar::tab {
    background-color: #0a0a20; border: 1px solid #1e3040;
    border-bottom: none; border-radius: 8px 8px 0 0;
    padding: 9px 18px; color: #1e3040;
}
QTabBar::tab:selected { background-color: #1a1a3a; color: #ff2d78; }
QTabBar::tab:hover    { background-color: #1a1a3a; color: #00d4ff; }
QMenu {
    background: #0a0a20; color: #b0e8ff;
    border: 1px solid #1e3040; border-radius: 8px; padding: 6px;
}
QMenu::item { padding: 8px 20px; border-radius: 6px; }
QMenu::item:selected { background: #1a1a3a; color: #ff2d78; }
QMenu::separator { background: #1e3040; height: 1px; margin: 4px 0; }
QMessageBox { background-color: #060612; }
QMessageBox QLabel { color: #b0e8ff; }
"""

# ── Sidebar styles ────────────────────────────────────────────────────────────
DARK_SIDEBAR_STYLE = """
QWidget {
    background-color: #0a0a14;
    border-right: 1px solid #1a1a28;
}
QPushButton {
    text-align: left;
    padding: 0 0 0 20px;
    border: none;
    border-radius: 0;
    background: transparent;
    color: #6666888;
    font-size: 13px;
    font-weight: 400;
}
QPushButton:hover {
    background-color: #14142a;
    color: #dde1f0;
}
QPushButton:checked {
    background-color: #1a1a30;
    color: #ffffff;
    border-left: 3px solid #4f8ef7;
    padding-left: 17px;
}
QPushButton:disabled {
    background: transparent;
    color: #dde1f0;
    border: none;
}
"""

LIGHT_SIDEBAR_STYLE = """
QWidget {
    background-color: #ffffff;
    border-right: 1px solid #e5e5ea;
}
QPushButton {
    text-align: left;
    padding: 0 0 0 20px;
    border: none;
    border-radius: 0;
    background: transparent;
    color: #8e8e93;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #f2f2f7;
    color: #1c1c1e;
}
QPushButton:checked {
    background-color: #e8e8ed;
    color: #1c1c1e;
    border-left: 3px solid #007aff;
    padding-left: 17px;
}
QPushButton:disabled {
    background: transparent;
    color: #1c1c1e;
    border: none;
}
"""

CYBER_SIDEBAR_STYLE = """
QWidget {
    background-color: #08081a;
    border-right: 1px solid #1e3040;
}
QPushButton {
    text-align: left;
    padding: 0 0 0 20px;
    border: none;
    border-radius: 0;
    background: transparent;
    color: #1e3040;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #0f0f28;
    color: #00d4ff;
}
QPushButton:checked {
    background-color: #1a1a3a;
    color: #ff2d78;
    border-left: 3px solid #ff2d78;
    padding-left: 17px;
}
QPushButton:disabled {
    background: transparent;
    color: #b0e8ff;
    border: none;
}
"""
