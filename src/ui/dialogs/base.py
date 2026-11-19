"""Kerangka dasar semua dialog: header, body, footer."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui.theme import bind_icon, bind_pixmap


class BaseDialog(QDialog):
    """Kerangka: header opsional, body (self.body), footer (self.footer)."""

    def __init__(self, title: str, subtitle: str = "", icon_name: str | None = None,
                 parent=None, modal: bool = True, header: bool = True):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        if icon_name:
            bind_icon(self, "setWindowIcon", icon_name, "ACCENT", "ACCENT")
        self.setModal(modal)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        if header:
            hdr = QFrame()
            hdr.setObjectName("dialogHeader")
            hl = QHBoxLayout(hdr)
            hl.setContentsMargins(22, 16, 22, 16)
            hl.setSpacing(14)
            if icon_name:
                glyph = QLabel()
                bind_pixmap(glyph, "setPixmap", icon_name, "ACCENT", 26)
                hl.addWidget(glyph)
            col = QVBoxLayout()
            col.setSpacing(2)
            t = QLabel(title)
            t.setObjectName("dialogTitle")
            col.addWidget(t)
            if subtitle:
                s = QLabel(subtitle)
                s.setObjectName("dialogSubtitle")
                col.addWidget(s)
            hl.addLayout(col, 1)
            root.addWidget(hdr)

        body = QWidget()
        self.body = QVBoxLayout(body)
        self.body.setContentsMargins(22, 18, 22, 18)
        self.body.setSpacing(10)
        root.addWidget(body, 1)

        footer = QFrame()
        footer.setObjectName("dialogFooter")
        self.footer = QHBoxLayout(footer)
        self.footer.setContentsMargins(16, 12, 16, 12)
        self.footer.setSpacing(8)
        root.addWidget(footer)

        self._note_timer = QTimer(self)
        self._note_timer.setSingleShot(True)
