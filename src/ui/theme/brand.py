"""Logo aplikasi: dimuat dari ``assets/icons`` (``logo.png`` + ``32/64/128/256.ico``).

Menggantikan logo sementara yang dulu digambar lewat QPainter. Logo sekarang gambar tetap (tidak ikut warna
tema), jadi tidak perlu lagi dibungkus ``bind_themed``.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

from services.paths import ICONS_DIR

LOGO_FILE = ICONS_DIR / "logo.png"
ICON_SIZES = (32, 64, 128, 256)            # ada file ICONS_DIR / "<ukuran>.ico" untuk tiap ukuran ini

_logo_cache: QPixmap | None = None
_icon_cache: QIcon | None = None


def _logo() -> QPixmap:
    """``logo.png`` ukuran asli (dibaca sekali). Pixmap kosong bila file hilang / rusak."""
    global _logo_cache
    if _logo_cache is None:
        _logo_cache = QPixmap(str(LOGO_FILE))
    return _logo_cache


def brand_pixmap(size: int = 256) -> QPixmap:
    """Logo berukuran ``size`` x ``size`` px (transparan di luar lingkaran). Kosong-transparan bila file logo hilang."""
    logo = _logo()
    if logo.isNull():
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)
        return pm
    return logo.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)


def brand_pixmap_hidpi(logical_size: int, dpr: float) -> QPixmap:
    """Logo untuk label/dialog: ukuran logis ``logical_size`` px, tajam di layar HiDPI."""
    pm = brand_pixmap(int(logical_size * dpr))
    pm.setDevicePixelRatio(dpr)
    return pm


def app_icon() -> QIcon:
    """Ikon aplikasi (jendela utama, taskbar, Alt-Tab). Tiap ukuran memakai file .ico-nya sendiri supaya tetap
    tajam di ukuran kecil; ``logo.png`` melengkapi ukuran lain / layar HiDPI. Harus dipanggil setelah QApplication dibuat."""
    global _icon_cache
    if _icon_cache is None:
        ic = QIcon()
        for size in ICON_SIZES:
            path = ICONS_DIR / f"{size}.ico"
            if path.is_file():
                ic.addFile(str(path))
        if LOGO_FILE.is_file():
            ic.addFile(str(LOGO_FILE))
        _icon_cache = ic
    return _icon_cache
