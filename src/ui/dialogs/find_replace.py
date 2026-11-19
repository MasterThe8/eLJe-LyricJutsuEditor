"""Dialog Find dan Replace."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QLineEdit

from ui.dialogs.base import BaseDialog
from ui.widgets.common import add_line_edit_icon, field_label, make_button


# ─────────────────────────────────────────────────────────────────────────────
#  Find
# ─────────────────────────────────────────────────────────────────────────────
class FindDialog(BaseDialog):
    """Non-modal. Signal: find_requested(text, backward, match_case, whole_word)."""
    find_requested = Signal(str, bool, bool, bool)

    def __init__(self, parent=None):
        super().__init__("Find Text", icon_name="find", parent=parent, modal=False, header=False)
        self.setMinimumWidth(460)

        self.body.addWidget(field_label("Find what"))
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Text to find…")
        self.line_edit.setClearButtonEnabled(True)
        add_line_edit_icon(self.line_edit, "find", QLineEdit.ActionPosition.LeadingPosition)
        self.body.addWidget(self.line_edit)

        opts = QHBoxLayout()
        opts.setSpacing(16)
        self.match_case = QCheckBox("Match case")
        self.whole_word = QCheckBox("Whole word")
        self.status = QLabel("")
        self.status.setObjectName("errorNote")
        opts.addWidget(self.match_case)
        opts.addWidget(self.whole_word)
        opts.addStretch(1)
        opts.addWidget(self.status)
        self.body.addLayout(opts)

        self.close_btn = make_button("Close", "ghost")
        self.prev_btn = make_button("Previous", "", "chevron_up")
        self.next_btn = make_button("Find Next", "primary")
        self.next_btn.setDefault(True)
        self.footer.addWidget(self.close_btn)
        self.footer.addStretch(1)
        self.footer.addWidget(self.prev_btn)
        self.footer.addWidget(self.next_btn)

        self.close_btn.clicked.connect(self.close)
        self.prev_btn.clicked.connect(lambda: self._emit(True))
        self.next_btn.clicked.connect(lambda: self._emit(False))
        self.line_edit.textChanged.connect(self._on_text)
        self._on_text("")

    def text(self) -> str:
        return self.line_edit.text()

    def set_status(self, message: str) -> None:
        self.status.setText(message)

    def _on_text(self, text: str) -> None:
        has = bool(text)
        self.next_btn.setEnabled(has)
        self.prev_btn.setEnabled(has)
        self.status.setText("")

    def _emit(self, backward: bool) -> None:
        if self.text():
            self.find_requested.emit(self.text(), backward,
                                     self.match_case.isChecked(), self.whole_word.isChecked())

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.line_edit.setFocus()
        self.line_edit.selectAll()


# ─────────────────────────────────────────────────────────────────────────────
#  Replace
# ─────────────────────────────────────────────────────────────────────────────
class ReplaceDialog(BaseDialog):
    """Modal. Signal: replace_all_requested(text, replacement, match_case)."""
    replace_all_requested = Signal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__("Replace", icon_name="replace", parent=parent, modal=True, header=False)
        self.setMinimumWidth(460)

        self.body.addWidget(field_label("Text"))
        self.original = QLineEdit()
        self.original.setPlaceholderText("Text to replace…")
        self.original.setClearButtonEnabled(True)
        add_line_edit_icon(self.original, "find", QLineEdit.ActionPosition.LeadingPosition)
        self.body.addWidget(self.original)

        self.body.addSpacing(2)
        self.body.addWidget(field_label("Replace with"))
        self.replacement = QLineEdit()
        self.replacement.setPlaceholderText("New text…")
        self.replacement.setClearButtonEnabled(True)
        add_line_edit_icon(self.replacement, "replace", QLineEdit.ActionPosition.LeadingPosition)
        self.body.addWidget(self.replacement)

        row = QHBoxLayout()
        self.match_case = QCheckBox("Match case")
        row.addWidget(self.match_case)
        row.addStretch(1)
        self.body.addLayout(row)
        self.body.addWidget(field_label("Replaces every match in the PlainText tab.", "fieldHint"))

        self.cancel_btn = make_button("Cancel", "ghost")
        self.replace_btn = make_button("Replace All", "primary")
        self.replace_btn.setDefault(True)
        self.footer.addStretch(1)
        self.footer.addWidget(self.cancel_btn)
        self.footer.addWidget(self.replace_btn)

        self.cancel_btn.clicked.connect(self.reject)
        self.replace_btn.clicked.connect(self._submit)
        self.original.textChanged.connect(self._validate)
        self.replacement.textChanged.connect(self._validate)
        self._validate()

    def _validate(self) -> None:
        # Sama seperti aslinya: tombol aktif bila kedua kolom terisi.
        self.replace_btn.setEnabled(bool(self.original.text() and self.replacement.text()))

    def _submit(self) -> None:
        self.replace_all_requested.emit(self.original.text(), self.replacement.text(),
                                        self.match_case.isChecked())
        self.accept()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.original.setFocus()
