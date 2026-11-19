"""Ilustrasi layar lirik mini untuk dialog Jutsu."""
from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from ui.theme import Theme, theme_events, to_qcolor


# ─────────────────────────────────────────────────────────────────────────────
#  Ilustrasi: layar lirik mini
# ─────────────────────────────────────────────────────────────────────────────
class LyricScreenMock(QWidget):
    """Layar lirik mini. state baris kedua: "shown" | "hidden" | "extra"."""

    PREFERRED_HEIGHT = 120          # tinggi awal; boleh menyusut ke MIN_HEIGHT / tumbuh ke MAX_HEIGHT
    MIN_HEIGHT = 100
    MAX_HEIGHT = 200

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(self.MIN_HEIGHT)
        self.setMaximumHeight(self.MAX_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._color: QColor | None = None          # None = warna teks bawaan tema (mengikuti tema)
        self._state = "shown"
        self._line1 = "Current phrase"
        self._line2 = "Next phrase"
        theme_events.changed.connect(self._on_theme_changed)

    def sizeHint(self) -> QSize:
        return QSize(320, self.PREFERRED_HEIGHT)

    def minimumSizeHint(self) -> QSize:
        return QSize(200, self.MIN_HEIGHT)

    def _on_theme_changed(self, _theme_id: str = "") -> None:
        self.update()

    def set_look(self, state: str | None = None, color: str | None = None,
                 line1: str | None = None, line2: str | None = None) -> None:
        if state is not None:
            self._state = state
        if color is not None:
            self._color = QColor(color)
        if line1 is not None:
            self._line1 = line1 or "Current phrase"
        if line2 is not None:
            self._line2 = line2 or "Next phrase"
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setPen(QPen(QColor(Theme.BORDER), 1))
        p.setBrush(to_qcolor(Theme.MOCK_SCREEN))
        p.drawRoundedRect(r, 12, 12)

        # Ukuran mengikuti tinggi widget supaya ilustrasi tetap proporsional saat window berubah ukuran.
        scale = max(0.85, min(1.2, r.height() / 130.0))
        font = QFont(self.font())
        font.setPointSizeF(16 * scale)
        font.setBold(True)
        p.setFont(font)
        fm = p.fontMetrics()
        row_h = fm.height() + 8.0
        gap = row_h * 0.45
        pad = 16.0
        avail_w = max(40.0, r.width() - 2 * pad)
        top = r.center().y() - (2 * row_h + gap) / 2          # dua baris + celah, dipusatkan vertikal
        elide = lambda text: fm.elidedText(text, Qt.TextElideMode.ElideRight, int(avail_w))   # noqa: E731

        p.setPen(self._color if self._color is not None else QColor(Theme.TEXT))   # warna lirik pengguna menang
        p.drawText(QRectF(r.left() + pad, top, avail_w, row_h), Qt.AlignmentFlag.AlignCenter, elide(self._line1))

        y2 = top + row_h + gap
        row2 = QRectF(r.left() + pad, y2, avail_w, row_h)
        if self._state == "hidden":
            pen = QPen(QColor(Theme.FAINT), 1)
            pen.setStyle(Qt.PenStyle.DashLine)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            bw = min(180.0, avail_w)
            box = QRectF(r.center().x() - bw / 2, y2 + 4, bw, row_h - 8)
            p.drawRoundedRect(box, 8, 8)
            small = QFont(font)
            small.setPointSizeF(9 * scale)
            small.setBold(False)
            p.setFont(small)
            p.drawText(box, Qt.AlignmentFlag.AlignCenter, "hidden")
        elif self._state == "extra":
            p.setPen(QColor(Theme.ACCENT))
            text = elide(self._line2)
            p.drawText(row2, Qt.AlignmentFlag.AlignCenter, text)
            w = fm.horizontalAdvance(text)
            p.setPen(QPen(QColor(Theme.ACCENT), 2))
            ul = row2.center().y() + fm.height() / 2
            p.drawLine(int(r.center().x() - w / 2), int(ul), int(r.center().x() + w / 2), int(ul))
        else:
            p.setPen(QColor(Theme.DIM))
            p.drawText(row2, Qt.AlignmentFlag.AlignCenter, elide(self._line2))
