"""Tombol persegi yang menampilkan warna dan membuka dialog pemilih warna."""
from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QPushButton

from ui.dialogs.color_dialog import ColorDialog
from ui.theme import Theme, theme_events


# ─────────────────────────────────────────────────────────────────────────────
#  Highlight
# ─────────────────────────────────────────────────────────────────────────────
class ColorField(QPushButton):
    """Tombol berisi swatch + kode hex; klik membuka ColorDialog."""
    changed = Signal(str)

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.setObjectName("colorField")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(150)
        self._color = "#000000"
        self.set_color(color)
        self.clicked.connect(self._pick)
        theme_events.changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, _theme_id: str = "") -> None:
        self.set_color(self._color)            # gambar ulang swatch; nilai warna pengguna tidak berubah

    def color(self) -> str:
        return self._color

    def set_color(self, hex_: str) -> None:
        self._color = QColor(hex_).name().upper()
        pm = QPixmap(36, 36)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(Theme.BORDER_HI), 2))
        p.setBrush(QColor(self._color))
        p.drawRoundedRect(QRectF(2, 2, 32, 32), 9, 9)
        p.end()
        pm.setDevicePixelRatio(2.0)
        self.setIcon(QIcon(pm))
        self.setIconSize(QSize(18, 18))
        self.setText("  " + self._color)

    def _pick(self) -> None:
        c = ColorDialog.get_color(QColor(self._color), self.window(), "Select Color")
        if c.isValid():
            self.set_color(c.name())
            self.changed.emit(self._color)
