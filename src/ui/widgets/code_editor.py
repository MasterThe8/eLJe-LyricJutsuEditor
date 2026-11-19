"""Editor teks dengan nomor baris, highlight baris aktif, dan penanda baris yang tidak valid."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QEvent, QRect, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QTextFormat
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QToolTip, QWidget

from ui.theme import Theme, theme_events, to_qcolor


# ─────────────────────────────────────────────────────────────────────────────
#  Editor dengan nomor baris + highlight baris aktif
# ─────────────────────────────────────────────────────────────────────────────
class _Gutter(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.gutter_width(), 0)

    def paintEvent(self, event) -> None:
        self._editor.paint_gutter(event)


class CodeEditor(QPlainTextEdit):
    # Pemeriksa baris opsional: ``checker(teks_baris) -> pesan_error | None``. Atribut kelas (bukan hanya di __init__)
    # supaya aman dibaca walau paint pertama datang sebelum __init__ selesai.
    _line_checker: Callable[[str], str | None] | None = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._gutter = _Gutter(self)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setCursorWidth(2)
        self.document().setDocumentMargin(12)
        self.blockCountChanged.connect(self._update_gutter_width)
        self.updateRequest.connect(self._update_gutter)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        theme_events.changed.connect(self._on_theme_changed)
        self._update_gutter_width()
        self._highlight_current_line()

    def _on_theme_changed(self, _theme_id: str = "") -> None:
        """Gutter & sorotan baris digambar manual (QPainter) → harus digambar ulang."""
        self._highlight_current_line()          # warna sorotan baris dari token; juga update gutter
        self.viewport().update()

    # -- gutter ----------------------------------------------------------
    def gutter_width(self) -> int:
        digits = max(3, len(str(max(1, self.blockCount()))))
        return 26 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_gutter_width(self, _count: int = 0) -> None:
        self.setViewportMargins(self.gutter_width(), 0, 0, 0)

    def _update_gutter(self, rect: QRect, dy: int) -> None:
        if dy:
            self._gutter.scroll(0, dy)
        else:
            self._gutter.update(0, rect.y(), self._gutter.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_gutter_width()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if not hasattr(self, "_gutter"):
            return
        cr = self.contentsRect()
        self._gutter.setGeometry(QRect(cr.left(), cr.top(), self.gutter_width(), cr.height()))

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if hasattr(self, "_gutter") and event.type() == QEvent.Type.FontChange:
            self._update_gutter_width()
            self._gutter.update()

    def paint_gutter(self, event) -> None:
        p = QPainter(self._gutter)
        p.fillRect(event.rect(), QColor(Theme.GUTTER))
        p.setPen(QColor(Theme.BORDER))
        p.drawLine(self._gutter.width() - 1, event.rect().top(),
                   self._gutter.width() - 1, event.rect().bottom())
        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        current = self.textCursor().blockNumber()
        line_h = self.fontMetrics().height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                p.setPen(QColor(Theme.TEXT if number == current else Theme.FAINT))
                p.drawText(0, top, self._gutter.width() - 12, line_h,
                           Qt.AlignmentFlag.AlignRight, str(number + 1))
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            number += 1

    # -- baris tidak valid -----------------------------------------------
    def set_line_checker(self, checker: Callable[[str], str | None] | None) -> None:
        """Pasang (atau lepas dengan ``None``) pemeriksa baris.

        ``checker`` menerima teks satu baris dan mengembalikan pesan kesalahan, atau ``None`` bila baris valid.
        Baris yang gagal digambar dengan latar ``Theme.ERROR_LINE`` selebar editor, dan pesannya tampil sebagai
        tooltip saat kursor mouse berada di baris itu. Pemeriksaan hanya dijalankan untuk baris yang sedang tampil
        saat paint, jadi tidak ada state yang perlu disinkronkan dan dokumen besar tetap ringan.
        """
        self._line_checker = checker
        self.viewport().update()

    def paintEvent(self, event) -> None:
        # Latar merah digambar SEBELUM super(): teks, seleksi, dan sorotan baris aktif (translusen) tergambar di atasnya.
        if self._line_checker is not None:
            self._paint_invalid_lines(event.rect())
        super().paintEvent(event)

    def _paint_invalid_lines(self, dirty: QRect) -> None:
        painter = QPainter(self.viewport())
        try:
            color = to_qcolor(Theme.ERROR_LINE)
            width = self.viewport().width()
            offset = self.contentOffset()
            block = self.firstVisibleBlock()
            while block.isValid():
                geo = self.blockBoundingGeometry(block).translated(offset)   # posisi tiap blok dihitung ulang (tinggi bisa pecahan)
                if geo.top() > dirty.bottom():
                    break
                if block.isVisible() and geo.bottom() >= dirty.top() and self._line_checker(block.text()):
                    painter.fillRect(QRectF(0, geo.top(), width, geo.height()), color)
                block = block.next()
        finally:
            painter.end()       # harus selesai sebelum super().paintEvent membuka QPainter-nya sendiri

    def viewportEvent(self, event) -> bool:
        """Tooltip alasan kesalahan di atas baris yang ditandai merah."""
        if event.type() == QEvent.Type.ToolTip and self._line_checker is not None:
            pos = event.pos()                                     # koordinat viewport
            block = self.cursorForPosition(pos).block()
            geo = self.blockBoundingGeometry(block).translated(self.contentOffset())
            problem = self._line_checker(block.text()) if geo.top() <= pos.y() <= geo.bottom() else None
            if problem:
                QToolTip.showText(event.globalPos(), problem, self.viewport())
            else:
                QToolTip.hideText()
                event.ignore()
            return True
        return super().viewportEvent(event)

    # -- current line ----------------------------------------------------
    def _highlight_current_line(self) -> None:
        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(to_qcolor(Theme.LINE_HIGHLIGHT))
        sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        sel.cursor = self.textCursor()
        sel.cursor.clearSelection()
        self.setExtraSelections([sel])
        self._gutter.update()
