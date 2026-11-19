"""Widget gambar untuk pemilih warna (kotak S/V, slider hue, pratinjau)."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from ui.theme import Theme, theme_events


class SVPicker(QWidget):
    """Kotak saturation (kiri→kanan) × value (bawah→atas) untuk hue tertentu."""
    changed = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._h, self._s, self._v = 0, 255, 255
        self.setMinimumSize(260, 170)
        self.setCursor(Qt.CursorShape.CrossCursor)
        theme_events.changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, _theme_id: str = "") -> None:
        self.update()

    def set_hsv(self, h: int, s: int, v: int) -> None:
        self._h, self._s, self._v = h, s, v
        self.update()

    def _rect(self) -> QRectF:
        return QRectF(self.rect()).adjusted(1, 1, -1, -1)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self._rect()
        path = QPainterPath()
        path.addRoundedRect(r, 9, 9)
        p.setClipPath(path)
        p.fillRect(r, QColor.fromHsv(self._h, 255, 255))
        gx = QLinearGradient(r.left(), 0, r.right(), 0)
        gx.setColorAt(0, QColor(255, 255, 255, 255))
        gx.setColorAt(1, QColor(255, 255, 255, 0))
        p.fillRect(r, QBrush(gx))
        gy = QLinearGradient(0, r.top(), 0, r.bottom())
        gy.setColorAt(0, QColor(0, 0, 0, 0))
        gy.setColorAt(1, QColor(0, 0, 0, 255))
        p.fillRect(r, QBrush(gy))
        p.setClipping(False)
        p.setPen(QPen(QColor(Theme.BORDER), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        x = r.left() + self._s / 255 * r.width()
        y = r.top() + (1 - self._v / 255) * r.height()
        p.setPen(QPen(QColor(0, 0, 0, 150), 1))
        p.drawEllipse(QPointF(x, y), 9, 9)
        p.setPen(QPen(QColor("#ffffff"), 2))
        p.drawEllipse(QPointF(x, y), 7, 7)

    def _pick(self, pos: QPointF) -> None:
        r = self._rect()
        s = int(max(0.0, min(1.0, (pos.x() - r.left()) / r.width())) * 255)
        v = int((1 - max(0.0, min(1.0, (pos.y() - r.top()) / r.height()))) * 255)
        self.changed.emit(s, v)

    def mousePressEvent(self, e) -> None:
        self._pick(e.position())

    def mouseMoveEvent(self, e) -> None:
        self._pick(e.position())


class HueSlider(QWidget):
    changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._h = 0
        self.setFixedHeight(22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_hue(self, h: int) -> None:
        self._h = h
        self.update()

    def _bar(self) -> QRectF:
        return QRectF(9, self.height() / 2 - 6, self.width() - 18, 12)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bar = self._bar()
        g = QLinearGradient(bar.left(), 0, bar.right(), 0)
        for i in range(7):
            g.setColorAt(i / 6, QColor.fromHsv(min(i * 60, 359), 255, 255))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawRoundedRect(bar, 6, 6)
        x = bar.left() + self._h / 359 * bar.width()
        p.setPen(QPen(QColor("#ffffff"), 2))
        p.setBrush(QColor.fromHsv(self._h, 255, 255))
        p.drawEllipse(QPointF(x, bar.center().y()), 8, 8)

    def _pick(self, pos: QPointF) -> None:
        bar = self._bar()
        t = max(0.0, min(1.0, (pos.x() - bar.left()) / bar.width()))
        self.changed.emit(int(t * 359))

    def mousePressEvent(self, e) -> None:
        self._pick(e.position())

    def mouseMoveEvent(self, e) -> None:
        self._pick(e.position())


class PreviewSwatch(QWidget):
    """Dua separuh: warna sekarang (kiri) dan warna baru (kanan)."""

    def __init__(self, current: QColor, parent=None):
        super().__init__(parent)
        self._old, self._new = QColor(current), QColor(current)
        self.setFixedHeight(56)
        theme_events.changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, _theme_id: str = "") -> None:
        self.update()

    def set_new(self, color: QColor) -> None:
        self._new = QColor(color)
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(r, 10, 10)
        p.setClipPath(path)
        half = r.width() / 2
        p.fillRect(QRectF(r.left(), r.top(), half, r.height()), self._old)
        p.fillRect(QRectF(r.left() + half, r.top(), half, r.height()), self._new)
        p.setClipping(False)
        p.setPen(QPen(QColor(Theme.BORDER_HI), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
