from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from services.constants import APP_VERSION
from services.settings import load_settings
from ui.main_window import MainWindow
from ui.theme import ThemeManager, app_icon


def _set_windows_app_id() -> None:
    """Windows: tanpa AppUserModelID sendiri, taskbar mengelompokkan jendela di bawah ikon python.exe, bukan logo eLJe."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MasterThe8.eLJe.LyricJutsuEditor")
    except (AttributeError, OSError):
        pass


def main() -> int:
    _set_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName("eLJe")
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")
    app.setWindowIcon(app_icon())      # ikon bawaan semua jendela (utama, dialog, Live Preview) bila tak punya ikon sendiri

    ui_font = QFont()
    ui_font.setFamilies(["Inter", "Segoe UI Variable Text", "Segoe UI", "SF Pro Text",
                         "Noto Sans", "Helvetica Neue", "Arial"])
    ui_font.setPointSizeF(10)
    app.setFont(ui_font)

    # Setting tersimpan (highlight, hotkey, font, panel, folder, …) dimuat SEBELUM jendela dibuat: semuanya dibaca saat
    # MainWindow dibangun. Nilai rusak/hilang otomatis kembali ke bawaan per-kunci.
    load_settings()

    # Tema: ThemeManager (child QApplication → hidup selama aplikasi berjalan) memuat ID tersimpan,
    # memvalidasinya (fallback 'default'), lalu menerapkan token + palet + QSS sebelum jendela dibuat.
    theme_manager = ThemeManager(app)
    theme_manager.apply_saved_theme()

    win = MainWindow(theme_manager)
    win.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
