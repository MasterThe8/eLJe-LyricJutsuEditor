"""Dialog UI Batch Jutsu: pemilihan target dan tabel lirik.

Dialog ini menyiapkan payload Batch Jutsu. Pembangkitan dan penerapan event ke chart
merupakan tahap terpisah; dialog hanya mengumpulkan target dan RowValues.
"""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMessageBox, QVBoxLayout

from core.operations.batch_jutsu import (
    BatchMode, BatchTarget, RowValues, carry_over_values, default_row_values,
    extract_targets, parse_target_input,
)
from core.operations.errors import JutsuError
from services.defaults import DEFAULT_HIGHLIGHT, DEFAULT_LYRIC
from ui.dialogs.operations.add_lyric import AddJutsuDialog
from ui.dialogs.operations.base import EventRow, JutsuDialog
from ui.dialogs.operations.lyric_input_table import LyricInputTableDialog
from ui.widgets.common import field_label, make_button


class BatchJutsuDialog(JutsuDialog):
    """Mengumpulkan target dan input lirik per target untuk Batch Jutsu."""

    NAMES = AddJutsuDialog.NAMES
    EVENT_ROWS = 5
    DEFAULT_WIDTH = 900

    MODE_TEXT = {
        BatchMode.SINGLE: (
            "Phrase start tick", "e.g. 1536",
            "Tick of a phrase_start event. Every lyric in that phrase becomes a row.",
        ),
        BatchMode.LIST: (
            "Tick list", "e.g. 1536, 1920, 2688",
            "Tick values separated by commas. Each one becomes a row.",
        ),
        BatchMode.RANGE: (
            "Tick range", "e.g. 1728 - 2304",
            "Start and end tick, both included. Every lyric inside the range becomes a row.",
        ),
    }

    script_provider: Callable[[], str] | None = None

    def __init__(self, parent=None):
        super().__init__(
            "Batch Jutsu",
            "Prepare Add Jutsu for multiple lines in one go.",
            "add",
            parent,
        )
        self._targets: list[BatchTarget] | None = None
        self._rows: list[RowValues] | None = None
        self._ready_key: tuple | None = None
        self._saved: dict | None = None

        # Mode diletakkan di atas field position yang disediakan JutsuDialog.
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([mode.value for mode in BatchMode])
        self.mode_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.form.insertLayout(0, self._field(QLabel("Select lines by"), self.mode_combo))

        self.target_hint = field_label("", "fieldHint", wrap=True)
        self.form.insertWidget(2, self.target_hint)

        # Mode List/Range menerima teks selain angka tunggal.
        self.position.setValidator(None)
        self.position_label.setText("Phrase start tick")

        self.combo = QComboBox()
        self.combo.addItems(self.NAMES)
        self.combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.form.addLayout(self._field(QLabel("Jutsu"), self.combo))

        self.input_btn = make_button("Input Lyric…", "", "lines")
        self.input_status = field_label("Not filled in yet.", "statusNote", wrap=True)
        lyrics_label = QLabel("Lyrics")
        lyrics_label.setObjectName("fieldLabel")
        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        button_row.addWidget(self.input_btn)
        button_row.addWidget(self.input_status, 1)
        lyrics_col = QVBoxLayout()
        lyrics_col.setSpacing(5)
        lyrics_col.addWidget(lyrics_label)
        lyrics_col.addLayout(button_row)
        self.form.addLayout(lyrics_col)

        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.combo.currentIndexChanged.connect(self._on_inputs_changed)
        self.input_btn.clicked.connect(self._open_table)

        self._ready = True
        self._on_mode_changed()

    def set_lyric_settings(self, lyric: dict, colors: dict) -> None:
        self._lyric = dict(DEFAULT_LYRIC, **lyric)
        self._colors = dict(DEFAULT_HIGHLIGHT, **colors)
        self._refresh()

    def _mode(self) -> BatchMode:
        return BatchMode(self.mode_combo.currentText())

    def _current_key(self) -> tuple:
        return (
            self.mode_combo.currentIndex(),
            self.position.text().strip(),
            self.combo.currentIndex(),
        )

    def _is_ready(self) -> bool:
        return self._rows is not None and self._ready_key == self._current_key()

    def _on_mode_changed(self, *_args) -> None:
        if not getattr(self, "_ready", False):
            return
        label, placeholder, hint = self.MODE_TEXT[self._mode()]
        self.position_label.setText(label)
        self.position.setPlaceholderText(placeholder)
        self.target_hint.setText(hint)
        self._on_inputs_changed()

    def _on_position(self, text: str) -> None:
        # Dipanggil dari JutsuDialog ketika teks target berubah.
        if not getattr(self, "_ready", False):
            return
        self._on_inputs_changed()

    def _on_inputs_changed(self, *_args) -> None:
        if not getattr(self, "_ready", False):
            return
        self._show_error("")
        self.input_btn.setEnabled(bool(self.position.text().strip()))
        ready = self._is_ready()
        self.apply_btn.setEnabled(ready)
        if ready:
            count = len(self._rows or [])
            self.input_status.setText(f"{count} line{'s' if count != 1 else ''} ready.")
        else:
            self.input_status.setText("Not filled in yet.")
        self._refresh()

    def _refresh(self, *_args) -> None:
        if not getattr(self, "_ready", False):
            return
        idx = self.combo.currentIndex()
        pos = lambda offset: self._pos(offset)  # noqa: E731
        rows: list[EventRow] = [
            (pos(0), "lyric", self._lyric["closing_lyric"]),
            (pos(1), "phrase_start", ""),
        ]
        if idx == 0:
            rows.append((pos(2), "lyric", "…"))
        else:
            middle = self._lyric["hidden_lyric"] if idx == 1 else "…"
            rows.extend([
                (pos(2), "lyric", middle),
                (pos(3), "phrase_start", ""),
                (pos(4), "lyric", "…"),
            ])
        self.events.set_rows(self._colors, rows)

    def _open_table(self) -> None:
        self._show_error("")
        if self.script_provider is None:
            QMessageBox.critical(self, "Error", "No chart script is available.")
            return
        try:
            spec = parse_target_input(self._mode(), self.position.text())
            targets = extract_targets(self.script_provider(), spec)
        except JutsuError as exc:
            QMessageBox.critical(self, "Error", str(exc))
            return

        jutsu = self.NAMES[self.combo.currentIndex()]
        defaults = [
            default_row_values(
                jutsu, target,
                self._lyric["closing_lyric"],
                self._lyric["hidden_lyric"],
            )
            for target in targets
        ]
        initial = self._seed_values(targets, jutsu, defaults)
        table = LyricInputTableDialog(jutsu, targets, initial, defaults, self)
        if not table.exec():
            return

        self._targets = targets
        self._rows = table.values()
        self._ready_key = self._current_key()
        self._saved = {
            "input": (self.mode_combo.currentIndex(), self.position.text().strip()),
            "jutsu": jutsu,
            "values": {target.position: value for target, value in zip(targets, self._rows)},
        }
        self._on_inputs_changed()

    def _seed_values(
        self,
        targets: list[BatchTarget],
        jutsu: str,
        defaults: list[RowValues],
    ) -> list[RowValues]:
        saved = self._saved
        if saved is None or saved["input"] != (
            self.mode_combo.currentIndex(), self.position.text().strip()
        ):
            return defaults
        same_jutsu = saved["jutsu"] == jutsu
        return [
            carry_over_values(default, saved["values"][target.position], same_jutsu)
            if target.position in saved["values"] else default
            for target, default in zip(targets, defaults)
        ]

    def validate(self) -> str:
        return "" if self._is_ready() else "Click Input Lyric and fill in the lyrics first."

    def collect(self) -> dict:
        return {
            "jutsu": self.NAMES[self.combo.currentIndex()],
            "mode": self._mode().value,
            "input": self.position.text().strip(),
            "targets": list(self._targets or []),
            "rows": list(self._rows or []),
        }
