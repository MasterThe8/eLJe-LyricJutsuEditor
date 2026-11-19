"""Penggambar teks bergaya game — dipakai bersama oleh Live Lyrics Preview dan judul Jutsu.

Qt rich-text (``QTextEdit`` / ``QLabel`` HTML) TIDAK punya padanan untuk tag TextMeshPro berikut, jadi teks
digambar sendiri dengan ``QPainter`` per karakter:

* ``<voffset=X>`` → baris dasar digeser (positif = naik); tidak mengubah lebar.
* ``<mspace=X>``  → tiap karakter memakai sel selebar X; TINTA glyph ditengahkan di sel (``mspace=1`` → huruf bertumpuk).
* ``<cspace=X>``  → tambahan X di belakang tiap karakter.

Semua nilai di ``Run`` sudah berupa pecahan em (lihat ``core.preview.phrase_display``), jadi di sini cukup dikali
ukuran font dalam piksel. Teks tanpa tag tata letak digambar utuh lewat ``drawText`` seperti sebelumnya.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtGui import QFont, QFontMetricsF, QPainter


class RunFonts:
    """Cache ``(QFont, QFontMetricsF)`` per kombinasi (bold, italic) pada satu ukuran piksel."""

    def __init__(self, base: QFont, px: int) -> None:
        self.base, self.px = base, max(6, int(px))
        self._cache: dict[tuple[bool, bool], tuple[QFont, QFontMetricsF]] = {}

    def get(self, bold: bool, italic: bool) -> tuple[QFont, QFontMetricsF]:
        key = (bold, italic)
        if key not in self._cache:
            font = QFont(self.base)
            font.setPixelSize(self.px)
            font.setBold(bold)
            font.setItalic(italic)
            self._cache[key] = (font, QFontMetricsF(font))
        return self._cache[key]


def measure_text(metrics: QFontMetricsF, text: str, size_px: float,
                 mspace: float | None = None, cspace: float = 0.0) -> float:
    """Lebar ``text`` (px). Tanpa mspace/cspace sama dengan ``horizontalAdvance`` biasa."""
    if mspace is None and not cspace:
        return metrics.horizontalAdvance(text)
    extra = cspace * size_px
    if mspace is not None:
        return len(text) * (mspace * size_px + extra)
    return sum(metrics.horizontalAdvance(ch) for ch in text) + len(text) * extra


def draw_text(painter: QPainter, metrics: QFontMetricsF, text: str, x: float, baseline: float,
              size_px: float, *, voffset: float = 0.0, mspace: float | None = None,
              cspace: float = 0.0) -> float:
    """Gambar ``text`` di (x, baseline) dengan font/pen yang sudah dipasang pada ``painter``.

    Mengembalikan x setelah teks (maju sebesar ``measure_text``), berguna untuk menggambar run berurutan.
    """
    y = baseline - voffset * size_px                      # voffset positif = naik
    if mspace is None and not cspace:
        painter.drawText(QPointF(x, y), text)
        return x + metrics.horizontalAdvance(text)

    extra = cspace * size_px
    cell = None if mspace is None else mspace * size_px
    for ch in text:
        visible = not ch.isspace()
        if cell is not None:
            if visible:
                ink = metrics.tightBoundingRect(ch)       # glyph ditengahkan menurut TINTA-nya, bukan kotak advance
                painter.drawText(QPointF(x + cell / 2.0 - (ink.left() + ink.width() / 2.0), y), ch)
            x += cell + extra
        else:
            if visible:
                painter.drawText(QPointF(x, y), ch)
            x += metrics.horizontalAdvance(ch) + extra
    return x
