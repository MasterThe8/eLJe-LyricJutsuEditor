"""Tema: token warna, registry tema, manager, ikon, logo, palet, stylesheet, dan font.

Modul luar mengimpor dari paket ini, bukan dari submodul.
"""
from .tokens import Theme, get_active_theme, set_active_theme, to_qcolor   # tokens harus pertama
from .brand import app_icon, brand_pixmap, brand_pixmap_hidpi
from .fonts import editor_font, font_for_symbol, mono_font, symbol_font
from .icons import bind_icon, bind_pixmap, bind_themed, icon, icon_pixmap, refresh_bound
from .manager import ThemeManager, theme_events
from .palette import apply_dark_palette
from .stylesheet import build_qss
from .themes import DEFAULT_THEME_ID, THEMES

__all__ = [
    "DEFAULT_THEME_ID", "THEMES", "Theme", "ThemeManager", "app_icon", "apply_dark_palette", "bind_icon",
    "bind_pixmap", "bind_themed", "brand_pixmap", "brand_pixmap_hidpi", "build_qss",
    "editor_font", "font_for_symbol", "get_active_theme", "icon", "icon_pixmap", "mono_font", "refresh_bound",
    "set_active_theme", "symbol_font", "theme_events", "to_qcolor",
]
