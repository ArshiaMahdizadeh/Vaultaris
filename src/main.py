import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase, QIcon
from src.utils.config import Config
from src.ui.themes.theme_manager import get_stylesheet

# Holds the Material Icons font family name after loading
MATERIAL_ICONS_FAMILY = None

# Resolved path to the assets directory (works both from source and PyInstaller bundle)
def _assets_dir() -> str:
    # PyInstaller unpacks to sys._MEIPASS at runtime
    base = getattr(sys, "_MEIPASS", os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base, "assets")


def load_material_icon_font():
    global MATERIAL_ICONS_FAMILY
    font_path = os.path.join(_assets_dir(), "fonts", "MaterialIcons-Regular.ttf")
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                MATERIAL_ICONS_FAMILY = families[0]


def load_app_icon(app: QApplication):
    """Set the application window icon from assets/icons/."""
    icons_dir = os.path.join(_assets_dir(), "icons")
    candidates = [
        os.path.join(icons_dir, "app.ico"),    # Windows
        os.path.join(icons_dir, "app.icns"),   # macOS
        os.path.join(icons_dir, "app.png"),    # Linux / fallback
        os.path.join(icons_dir, "app.svg"),    # vector fallback
    ]
    for path in candidates:
        if os.path.exists(path):
            app.setWindowIcon(QIcon(path))
            return


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Vaultaris")
    app.setOrganizationName("Vaultaris")
    app.setApplicationDisplayName("Vaultaris")

    load_material_icon_font()
    load_app_icon(app)

    theme = Config.get("theme", "dark")
    app.setStyleSheet(get_stylesheet(theme))

    from src.ui.windows.main_window import MainWindow
    window = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
