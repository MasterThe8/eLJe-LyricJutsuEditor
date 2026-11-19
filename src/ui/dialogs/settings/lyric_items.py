"""Dialog Setting › LyricJutsu (closing/hidden lyric)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout

from services.defaults import DEFAULT_HIGHLIGHT, DEFAULT_LYRIC
from ui.dialogs.settings.base import SettingsDialog
from ui.html_helpers import event_line_html
from ui.theme import mono_font
from ui.widgets.common import divider, field_label


# ─────────────────────────────────────────────────────────────────────────────
#  LyricJutsu
# ─────────────────────────────────────────────────────────────────────────────
class LyricSettingDialog(SettingsDialog):
    def __init__(self, values: dict | None = None, parent=None):
        super().__init__("Jutsu Lyric Setting", "Lyric events that the Jutsu tools insert for you.",
                         "lines", parent)
        self.setMinimumWidth(500)
        data = dict(DEFAULT_LYRIC, **(values or {}))
        self._colors = dict(DEFAULT_HIGHLIGHT)

        self.closing = QLineEdit(data["closing_lyric"])
        self.hidden = QLineEdit(data["hidden_lyric"])
        self.sample_closing = QLabel()
        self.sample_hidden = QLabel()
        specs = (
            ("Closing lyric", "The lyric event that marks where a lyric ends.", self.closing, self.sample_closing, "1152"),
            ("Hidden lyric", "The placeholder lyric event that stays out of the display.", self.hidden, self.sample_hidden, "1248"),
        )
        for i, (title, hint, edit, sample, _pos) in enumerate(specs):
            if i:
                self.body.addSpacing(6)
                self.body.addWidget(divider())
                self.body.addSpacing(6)
            head = QHBoxLayout()
            col = QVBoxLayout()
            col.setSpacing(2)
            col.addWidget(field_label(title, "sectionTitle"))
            col.addWidget(field_label(hint, "fieldHint"))
            head.addLayout(col, 1)
            edit.setFixedWidth(110)
            edit.setMaxLength(12)
            edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            edit.setFont(mono_font(12))
            head.addWidget(edit, 0, Qt.AlignmentFlag.AlignTop)
            self.body.addLayout(head)
            box = QFrame()
            box.setObjectName("previewBox")
            bl = QVBoxLayout(box)
            bl.setContentsMargins(14, 8, 14, 8)
            sample.setFont(mono_font(11))
            bl.addWidget(sample)
            self.body.addWidget(box)
            edit.textChanged.connect(self._refresh)
        self._refresh()

    def _refresh(self) -> None:
        self.sample_closing.setText(event_line_html(self._colors, "1152", "lyric", self.closing.text()))
        self.sample_hidden.setText(event_line_html(self._colors, "1248", "lyric", self.hidden.text()))

    def values(self) -> dict:
        return {"closing_lyric": self.closing.text(), "hidden_lyric": self.hidden.text()}

    def set_values(self, data: dict) -> None:
        self.closing.setText(data["closing_lyric"])
        self.hidden.setText(data["hidden_lyric"])

    def defaults(self) -> dict:
        return dict(DEFAULT_LYRIC)

    def set_preview_colors(self, colors: dict) -> None:
        self._colors = dict(colors)
        self._refresh()
