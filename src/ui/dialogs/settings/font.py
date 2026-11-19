"""Dialog Setting › Font."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ui.dialogs.base import BaseDialog
from ui.theme import Theme
from ui.widgets.common import add_line_edit_icon, field_label, make_button


# ─────────────────────────────────────────────────────────────────────────────
#  Font  (pengganti QFontDialog)
# ─────────────────────────────────────────────────────────────────────────────
class FontDialog(BaseDialog):
    SAMPLE = '768 = E "lyric Hold"\nThe quick brown fox jumps over the lazy dog 0123456789'
    STYLES = ["Regular", "Bold", "Italic", "Bold Italic"]
    SIZES = [8, 9, 10, 11, 12, 13, 14, 16, 18, 20, 24, 28, 32, 36, 48]

    def __init__(self, initial: QFont | None = None, parent=None):
        super().__init__("Editor Font", "Applies to the PlainText and Display tabs.", "font", parent)
        self.resize(620, 620)
        self.setMinimumSize(540, 560)
        initial = QFont(initial) if initial is not None else QFont()
        self._result: QFont | None = None
        self._family = initial.family()
        self._all = QFontDatabase.families()
        self._fixed: dict[str, bool] = {}

        # filter
        frow = QHBoxLayout()
        frow.setSpacing(14)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search fonts")
        self.search.setClearButtonEnabled(True)
        add_line_edit_icon(self.search, "find", QLineEdit.ActionPosition.LeadingPosition)
        self.mono_only = QCheckBox("Monospace only")
        frow.addWidget(self.search, 1)
        frow.addWidget(self.mono_only)
        self.body.addLayout(frow)

        # tiga kolom
        self.family_list = QListWidget()
        self.style_list = QListWidget()
        self.style_list.addItems(self.STYLES)
        self.style_list.setFixedWidth(130)
        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 72)
        self.size_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.size_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.size_list = QListWidget()
        self.size_list.addItems([str(s) for s in self.SIZES])

        size_col = QVBoxLayout()
        size_col.setSpacing(6)
        size_col.addWidget(self.size_spin)
        size_col.addWidget(self.size_list, 1)
        size_w = QWidget()
        size_w.setLayout(size_col)
        size_w.setFixedWidth(84)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)
        grid.addWidget(field_label("Font"), 0, 0)
        grid.addWidget(field_label("Style"), 0, 1)
        grid.addWidget(field_label("Size"), 0, 2)
        grid.addWidget(self.family_list, 1, 0)
        grid.addWidget(self.style_list, 1, 1)
        grid.addWidget(size_w, 1, 2)
        grid.setColumnStretch(0, 1)
        self.body.addLayout(grid, 1)

        # preview
        self.body.addWidget(field_label("Preview"))
        box = QFrame()
        box.setObjectName("previewBox")
        bl = QVBoxLayout(box)
        bl.setContentsMargins(16, 14, 16, 14)
        self.preview = QLabel(self.SAMPLE)
        self.preview.setWordWrap(True)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.preview.setStyleSheet(f"color: {Theme.EDITOR_TEXT};")
        self.preview.setMinimumHeight(86)
        bl.addWidget(self.preview)
        self.body.addWidget(box)

        self.cancel_btn = make_button("Cancel", "ghost")
        self.apply_btn = make_button("Apply", "primary", "check")
        self.apply_btn.setDefault(True)
        self.footer.addStretch(1)
        self.footer.addWidget(self.cancel_btn)
        self.footer.addWidget(self.apply_btn)

        # state awal
        self.size_spin.setValue(initial.pointSize() if initial.pointSize() > 0 else 13)
        self.style_list.setCurrentRow((1 if initial.bold() else 0) + (2 if initial.italic() else 0))
        self._refill()
        self._sync_size_list()
        self._update_preview()

        self.search.textChanged.connect(self._refill)
        self.mono_only.toggled.connect(self._refill)
        self.family_list.currentTextChanged.connect(self._on_family)
        self.style_list.currentRowChanged.connect(lambda _r: self._update_preview())
        self.size_spin.valueChanged.connect(self._on_size)
        self.size_list.itemClicked.connect(lambda it: self.size_spin.setValue(int(it.text())))
        self.cancel_btn.clicked.connect(self.reject)
        self.apply_btn.clicked.connect(self._accept)

    def _is_fixed(self, fam: str) -> bool:
        if fam not in self._fixed:
            self._fixed[fam] = QFontDatabase.isFixedPitch(fam)
        return self._fixed[fam]

    def _refill(self) -> None:
        needle = self.search.text().strip().lower()
        fams = [f for f in self._all
                if (not needle or needle in f.lower()) and (not self.mono_only.isChecked() or self._is_fixed(f))]
        self.family_list.blockSignals(True)
        self.family_list.clear()
        self.family_list.addItems(fams)
        if self._family in fams:
            self.family_list.setCurrentRow(fams.index(self._family))
            self.family_list.scrollToItem(self.family_list.currentItem(),
                                          QAbstractItemView.ScrollHint.PositionAtCenter)
        self.family_list.blockSignals(False)

    def _on_family(self, name: str) -> None:
        if name:
            self._family = name
            self._update_preview()

    def _on_size(self, _value: int) -> None:
        self._sync_size_list()
        self._update_preview()

    def _sync_size_list(self) -> None:
        self.size_list.blockSignals(True)
        v = self.size_spin.value()
        self.size_list.setCurrentRow(self.SIZES.index(v) if v in self.SIZES else -1)
        self.size_list.blockSignals(False)

    def _build_font(self) -> QFont:
        f = QFont(self._family)
        f.setPointSize(self.size_spin.value())
        row = self.style_list.currentRow()
        f.setBold(row in (1, 3))
        f.setItalic(row in (2, 3))
        return f

    def _update_preview(self) -> None:
        f = self._build_font()
        self.preview.setFont(f)

    def _accept(self) -> None:
        self._result = self._build_font()
        self.accept()

    @staticmethod
    def get_font(initial: QFont | None = None, parent=None) -> tuple[bool, QFont]:
        """Bentuk kembalian sama dengan PySide6 QFontDialog.getFont: (ok, font)."""
        dlg = FontDialog(initial, parent)
        dlg.exec()
        if dlg._result is not None:
            return True, QFont(dlg._result)
        return False, QFont(initial) if initial is not None else QFont()
