"""Dialog Setting › Highlight."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout

from services.defaults import DEFAULT_HIGHLIGHT
from ui.dialogs.settings.base import SettingsDialog
from ui.html_helpers import span
from ui.theme import mono_font
from ui.widgets.color_field import ColorField
from ui.widgets.common import field_label


class HighlightDialog(SettingsDialog):
    ROWS = [
        ("position", "Position", "768"),
        ("value", "Value", '"Hold"'),
        ("richtag", "Tag", "<b>"),
        ("eventname", "Event Name", "phrase_start"),
    ]

    def __init__(self, colors: dict | None = None, parent=None):
        super().__init__("Highlighter Setting", "Colors used to highlight the PlainText editor.",
                         "palette", parent)
        self.setMinimumWidth(500)
        colors = dict(DEFAULT_HIGHLIGHT, **(colors or {}))

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        self.fields: dict[str, ColorField] = {}
        self.samples: dict[str, QLabel] = {}
        mono = mono_font(11)
        for r, (key, label, sample) in enumerate(self.ROWS):
            lbl = QLabel(label)
            fld = ColorField(colors[key])
            smp = QLabel(sample)
            smp.setTextFormat(Qt.TextFormat.PlainText)
            smp.setFont(mono)
            fld.changed.connect(self._refresh)
            self.fields[key], self.samples[key] = fld, smp
            grid.addWidget(lbl, r, 0)
            grid.addWidget(fld, r, 1)
            grid.addWidget(smp, r, 2)
        grid.setColumnMinimumWidth(0, 96)
        grid.setColumnStretch(2, 1)
        self.body.addLayout(grid)

        self.body.addSpacing(8)
        self.body.addWidget(field_label("Preview"))
        box = QFrame()
        box.setObjectName("previewBox")
        bl = QVBoxLayout(box)
        bl.setContentsMargins(16, 12, 16, 12)
        self.preview = QLabel()
        self.preview.setFont(mono_font(12))
        self.preview.setTextFormat(Qt.TextFormat.RichText)
        bl.addWidget(self.preview)
        self.body.addWidget(box)
        self._refresh()

    def _refresh(self) -> None:
        c = self.values()
        for key, smp in self.samples.items():
            smp.setStyleSheet(f"color: {c[key]};")
        tag = lambda s: span(c["richtag"], s)           # noqa: E731
        val = lambda s: span(c["value"], s)             # noqa: E731
        line = (span(c["position"], "768") + " = E " + val('"') + span(c["eventname"], "lyric")
                + val(" ") + tag("<b>") + val("Hold") + tag("</b>") + val('"'))
        self.preview.setText(f"<pre style='margin:0'>{line}</pre>")

    def values(self) -> dict:
        return {k: f.color() for k, f in self.fields.items()}

    def set_values(self, data: dict) -> None:
        for k, f in self.fields.items():
            if k in data:
                f.set_color(data[k])
        self._refresh()

    def defaults(self) -> dict:
        return dict(DEFAULT_HIGHLIGHT)
