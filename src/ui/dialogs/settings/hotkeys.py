"""Dialog Setting › Hotkey."""
from __future__ import annotations

from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from services.defaults import DEFAULT_SHORTCUTS
from ui.dialogs.settings.base import SettingsDialog
from ui.widgets.common import divider, field_label

# ─────────────────────────────────────────────────────────────────────────────
#  Hotkey
# ─────────────────────────────────────────────────────────────────────────────
HOTKEY_COLUMNS = [
    [
        ("Panels", [("jutsueditor", "Jutsu Editor"), ("livepreview", "Live Lyrics Preview"),
                    ("toggle_display", "Display Toggle"), ("toggle_treeview", "Treeview Toggle"),
                    ("toggle_temptext", "Temptext Toggle")]),
        ("Tools", [("colorpicker", "Color Picker"), ("getsymbol", "Get Symbol"),
                   ("weirdtext", "Weird Text Generator")]),
        ("Jutsu", [("addjutsu", "Add Jutsu"), ("batchjutsu", "Batch Jutsu"),
                   ("colorjutsu1", "Color Jutsu (method 1)"), ("colorjutsu2", "Color Jutsu (method 2)"),
                   ("kan2romjutsu", "Kan2Rom Jutsu")]),
    ],
    [
        ("Rich text tags", [("b_tag", "b Tag"), ("i_tag", "i Tag"), ("color_tag", "color Tag"),
                            ("br_tag", "br Tag"), ("voffset_tag", "voffset Tag"),
                            ("smallcaps_tag", "smallcaps Tag"), ("lowercase_tag", "lowercase Tag"),
                            ("uppercase_tag", "uppercase Tag"), ("mspace_tag", "mspace Tag"),
                            ("cspace_tag", "cspace Tag"), ("sub_tag", "sub Tag"), ("sup_tag", "sup Tag")]),
    ],
]


class HotkeyDialog(SettingsDialog):
    def __init__(self, shortcuts: dict | None = None, parent=None):
        super().__init__("Hotkey Setting", "Click a field, then press the key combination you want.",
                         "keyboard", parent)
        self.resize(780, 660)
        self.setMinimumSize(700, 520)
        data = dict(DEFAULT_SHORTCUTS, **(shortcuts or {}))
        self.edits: dict[str, QKeySequenceEdit] = {}

        cols = QHBoxLayout()
        cols.setSpacing(24)
        for ci, groups in enumerate(HOTKEY_COLUMNS):
            if ci:
                cols.addWidget(divider(vertical=True))
            col = QVBoxLayout()
            col.setSpacing(6)
            for gi, (group, items) in enumerate(groups):
                if gi:
                    col.addSpacing(10)
                col.addWidget(field_label(group, "sectionTitle"))
                grid = QGridLayout()
                grid.setHorizontalSpacing(12)
                grid.setVerticalSpacing(6)
                for r, (key, label) in enumerate(items):
                    ed = QKeySequenceEdit(QKeySequence(data[key]))
                    ed.setFixedWidth(150)
                    if hasattr(ed, "setMaximumSequenceLength"):
                        ed.setMaximumSequenceLength(1)
                    if hasattr(ed, "setClearButtonEnabled"):
                        ed.setClearButtonEnabled(True)
                    ed.keySequenceChanged.connect(self._check_conflicts)
                    self.edits[key] = ed
                    grid.addWidget(QLabel(label), r, 0)
                    grid.addWidget(ed, r, 1)
                grid.setColumnStretch(0, 1)
                col.addLayout(grid)
            col.addStretch(1)
            cols.addLayout(col, 1)

        holder = QWidget()
        holder.setLayout(cols)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(holder)
        scroll.setStyleSheet("QScrollArea { background: transparent; } QScrollArea > QWidget > QWidget { background: transparent; }")
        self.body.addWidget(scroll, 1)

        self.conflict_note = QLabel("")
        self.conflict_note.setObjectName("errorNote")
        self.body.addWidget(self.conflict_note)
        self._check_conflicts()

    def _seq(self, key: str) -> str:
        return self.edits[key].keySequence().toString(QKeySequence.SequenceFormat.PortableText)

    def _check_conflicts(self) -> None:
        seen: dict[str, list[str]] = {}
        for key in self.edits:
            s = self._seq(key)
            if s:
                seen.setdefault(s, []).append(key)
        clashing = {k for keys in seen.values() if len(keys) > 1 for k in keys}
        for key, ed in self.edits.items():
            ed.setProperty("conflict", key in clashing)
            ed.style().unpolish(ed)
            ed.style().polish(ed)
        self.conflict_note.setText("Two or more actions share the same shortcut." if clashing else "")
        self.apply_btn.setEnabled(not clashing)

    def values(self) -> dict:
        return {k: self._seq(k) for k in self.edits}

    def set_values(self, data: dict) -> None:
        for k, ed in self.edits.items():
            if k in data:
                ed.setKeySequence(QKeySequence(data[k]))
        self._check_conflicts()

    def defaults(self) -> dict:
        return dict(DEFAULT_SHORTCUTS)
