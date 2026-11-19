"""Syntax highlighter untuk baris event di editor."""
from __future__ import annotations

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat

from services.settings import HIGHLIGHT


# ─────────────────────────────────────────────────────────────────────────────
#  Syntax highlighter  (QRegExp -> QRegularExpression)
# ─────────────────────────────────────────────────────────────────────────────
class LyricHighlighter(QSyntaxHighlighter):
    EVENT_NAMES = "Default|default|Section|section|phrase_start|phrase_end|lyric"

    def __init__(self, document, colors: dict = HIGHLIGHT):
        super().__init__(document)

        def fmt(color: str) -> QTextCharFormat:
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            return f

        # Urutan penting: aturan di belakang menimpa aturan di depan.
        # Nama event hanya kata PERTAMA setelah tanda kutip pembuka, mis. `864 = E "lyric the lyric"`:
        # hanya "lyric" pertama yang diwarnai; kata "lyric" di dalam value lirik tidak ikut.
        self._rules = [
            (QRegularExpression(r"\b[0-9_]+(?=\s*=)"), fmt(colors["position"])),
            (QRegularExpression(r'".*"'), fmt(colors["value"])),
            (QRegularExpression(r"<[^>]+>"), fmt(colors["richtag"])),
            (QRegularExpression(rf'(?<=")\s*(?:{self.EVENT_NAMES})\b'), fmt(colors["eventname"])),
        ]

    def highlightBlock(self, text: str) -> None:
        for regex, fmt in self._rules:
            it = regex.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)
