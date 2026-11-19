"""Pembantu grid simbol, dipakai bersama oleh jendela Get Symbol dan panel Symbol Picker.

Dua hal di sini memang disengaja, karena tanpa keduanya sebagian simbol tampil kosong:

* Ukuran item DIPAKU sama dengan sel grid. Tanpa ``setSizeHint``, ``QListView`` (dengan ``setUniformItemSizes``)
  memakai ukuran satu item saja untuk semuanya, yaitu selebar karakter sempit (±25 px), jadi kotak teks setiap sel
  menyempit dan highlight hanya menempel di kiri sel.
* Elide dimatikan (``configure_symbol_view``). Dengan kotak sempit tadi, glyph yang lebih lebar dari kotak itu
  (emoji ±1,5 em seperti 😀 🤣 🆗) dipotong Qt sampai habis, sehingga selnya kosong.
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QStandardItem
from PySide6.QtWidgets import QListView

from ui.theme import font_for_symbol

SYMBOL_CELL = 52            # sisi sel grid (px)
SYMBOL_POINT_SIZE = 17      # ukuran glyph di grid (pt)


def configure_symbol_view(view: QListView) -> None:
    """Pengaturan ``QListView`` yang wajib untuk grid simbol (ukuran sel, tanpa elide)."""
    view.setGridSize(QSize(SYMBOL_CELL, SYMBOL_CELL))
    view.setTextElideMode(Qt.TextElideMode.ElideNone)


def symbol_item(ch: str) -> QStandardItem:
    """Satu sel simbol: font terbaik untuk ``ch`` (lihat ``ui.theme.fonts``), ukuran = sel, tooltip kode."""
    item = QStandardItem(ch)
    item.setFont(font_for_symbol(ch, SYMBOL_POINT_SIZE))
    item.setSizeHint(QSize(SYMBOL_CELL, SYMBOL_CELL))
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    item.setToolTip(f"{ch}   U+{ord(ch):04X}")
    return item
