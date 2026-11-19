"""ThemeManager: satu-satunya jalur untuk mengganti tema aplikasi saat runtime."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from services.settings import load_theme_id, save_theme_id
from ui.theme.icons import refresh_bound
from ui.theme.palette import apply_dark_palette
from ui.theme.stylesheet import build_qss
from ui.theme.themes import DEFAULT_THEME_ID, THEMES
from ui.theme.tokens import set_active_theme


class ThemeEvents(QObject):
    """Pemancar sinyal global. Widget cukup ``theme_events.changed.connect(self._on_theme_changed)``
    tanpa perlu referensi ke ThemeManager."""
    changed = Signal(str)          # id tema baru


theme_events = ThemeEvents()


class ThemeManager(QObject):
    """Mengelola tema: validasi ID, token aktif, palet, QSS, ikon, notifikasi, dan penyimpanan.

    Dibuat sekali di app.py dan di-parent ke QApplication supaya hidup selama aplikasi berjalan."""
    theme_changed = Signal(str)

    def __init__(self, app: QApplication, parent: QObject | None = None):
        super().__init__(parent or app)
        self._app = app
        self._current: str | None = None
        self.theme_changed.connect(theme_events.changed)

    # -- registry ------------------------------------------------------------
    @property
    def current_theme(self) -> str:
        return self._current or DEFAULT_THEME_ID

    @staticmethod
    def is_valid(theme_id: object) -> bool:
        return isinstance(theme_id, str) and theme_id in THEMES

    @staticmethod
    def available_themes() -> list[dict]:
        """[{'id','name','description'}, ...] sesuai urutan registry."""
        return [{"id": t["id"], "name": t["name"], "description": t["description"]}
                for t in THEMES.values()]

    # -- penerapan -----------------------------------------------------------
    def apply_saved_theme(self) -> str:
        """Muat ID tersimpan; ID tak dikenal/rusak → 'default'. Mengembalikan ID yang diterapkan."""
        saved = load_theme_id()
        theme_id = saved if self.is_valid(saved) else DEFAULT_THEME_ID
        self.set_theme(theme_id, persist=False)
        return theme_id

    def set_theme(self, theme_id: str, persist: bool = True) -> bool:
        """Terapkan tema. False (tanpa mengubah apa pun) bila ID tidak valid."""
        if not self.is_valid(theme_id):
            return False
        if theme_id == self._current:
            if persist:
                save_theme_id(theme_id)
            return True
        set_active_theme(THEMES[theme_id]["colors"])        # 1. token aktif
        apply_dark_palette(self._app)                         # 2. QPalette
        self._app.setStyleSheet(build_qss())                  # 3. QSS universal
        refresh_bound()                                       # 4. ikon/pixmap bertema
        self._current = theme_id
        if persist:
            save_theme_id(theme_id)
        self.theme_changed.emit(theme_id)                     # 5. widget custom: repaint/refresh
        return True
