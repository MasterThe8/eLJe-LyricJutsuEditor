"""Jendela "Input Lyric" milik Batch Jutsu: tabel untuk mengedit lirik tiap target sebelum Jutsu dijalankan.

* Satu baris = satu target (satu tick). Tick tampil sebagai HEADER BARIS, bukan kolom, sehingga tabel tetap
  persis 2 kolom (No SlideUp) atau 3 kolom (Hide / Fake). Arahkan kursor ke tick untuk melihat
  baris asli chart-nya.
* Kolom dan nilai awal datang dari ``core.operations.batch_jutsu`` (``table_columns`` / ``default_row_values``);
  modul ini hanya menampilkan dan mengumpulkan hasil edit — tidak ada logika Jutsu di sini.
* Dialog modal (anak dari dialog Batch Jutsu). Modal disengaja: isi tabel bergantung pada mode, input target, dan
  pilihan Jutsu di dialog induk, jadi ketiganya tidak boleh berubah selagi tabel terbuka.
* OK hanya diterima bila semua sel terisi (``check_row_values``); sel pertama yang kosong disorot.
"""
from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QLabel, QTableWidget, QTableWidgetItem

from core.operations.batch_jutsu import (
    BatchTarget, RowValueError, RowValues, check_row_values, table_columns,
)
from core.operations.errors import JutsuError
from ui.dialogs.base import BaseDialog
from ui.widgets.common import field_label, make_button, soft_wrap


class LyricInputTableDialog(BaseDialog):
    """Tabel edit lirik. ``values()`` mengembalikan ``list[RowValues]`` (urutan = ``targets``) setelah OK."""

    MIN_WIDTH, MIN_HEIGHT = 560, 340
    DEFAULT_WIDTH = 680
    ROW_HEIGHT = 36
    COLUMN_WIDTH = 150                  # kolom Closing / Hide / Fake; kolom Lyric Input mengisi sisanya

    def __init__(self, jutsu: str, targets: Sequence[BatchTarget], values: Sequence[RowValues],
                 defaults: Sequence[RowValues], parent=None) -> None:
        """``values`` = isi awal tabel; ``defaults`` = isi yang dipulihkan tombol Reset (sama panjang dengan targets)."""
        super().__init__("Input Lyric", f"{jutsu} · edit the lyric of each selected line.", "lines", parent)
        self._jutsu = jutsu
        self._targets = list(targets)
        self._columns = table_columns(jutsu)
        self._defaults = list(defaults)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self._sized = False

        # ── tabel ───────────────────────────────────────────────────────────
        self.table = QTableWidget(len(self._targets), len(self._columns))
        self.table.setHorizontalHeaderLabels([c.title for c in self._columns])
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked
                                   | QAbstractItemView.EditTrigger.SelectedClicked
                                   | QAbstractItemView.EditTrigger.EditKeyPressed
                                   | QAbstractItemView.EditTrigger.AnyKeyPressed)   # langsung ketik = ganti isi sel
        self.table.setWordWrap(False)
        self.table.setShowGrid(True)
        self.table.verticalHeader().setDefaultSectionSize(self.ROW_HEIGHT)
        self.table.verticalHeader().setSectionsClickable(False)
        header = self.table.horizontalHeader()
        header.setSectionsClickable(False)
        header.setHighlightSections(False)
        last = len(self._columns) - 1
        for col in range(last):
            self.table.setColumnWidth(col, self.COLUMN_WIDTH)
        header.setSectionResizeMode(last, QHeaderView.ResizeMode.Stretch)

        for row, target in enumerate(self._targets):              # header baris = tick asli target
            tick = QTableWidgetItem(str(target.position))
            tick.setToolTip("Original line(s) in the chart:\n" + "\n".join(target.lines))
            self.table.setVerticalHeaderItem(row, tick)
        self._fill(values)

        hint = field_label("Double-click a cell, or select it and start typing. "
                           "The number at the start of each row is the tick of the original line.",
                           "fieldHint", wrap=True)
        self.body.addWidget(hint)
        self.body.addWidget(self.table, 1)

        # ── footer: error di kiri, tombol di kanan ──────────────────────────
        self.error = QLabel("")
        self.error.setObjectName("errorNote")
        soft_wrap(self.error)
        self.error.hide()
        self.reset_btn = make_button("Reset", "ghost", "reset")
        self.reset_btn.setToolTip("Restore the default values")
        self.cancel_btn = make_button("Cancel", "ghost")
        self.ok_btn = make_button("OK", "primary", "check")
        for button in (self.reset_btn, self.cancel_btn, self.ok_btn):
            button.setAutoDefault(False)         # Enter di tabel hanya untuk edit sel, jangan menekan OK diam-diam
        self.footer.addWidget(self.error, 1)
        self.footer.addWidget(self.reset_btn)
        self.footer.addWidget(self.cancel_btn)
        self.footer.addWidget(self.ok_btn)

        self.reset_btn.clicked.connect(self._reset)
        self.cancel_btn.clicked.connect(self.reject)
        self.ok_btn.clicked.connect(self._accept)
        self.table.itemChanged.connect(lambda _item: self._show_error(""))

        if self._targets:
            self.table.setCurrentCell(0, last)       # mulai dari kolom Lyric Input baris pertama

    # -- isi tabel -----------------------------------------------------------
    def _fill(self, values: Sequence[RowValues]) -> None:
        blocked = self.table.blockSignals(True)       # jangan memicu itemChanged saat mengisi
        for row, value in enumerate(values):
            for col, column in enumerate(self._columns):
                self.table.setItem(row, col, QTableWidgetItem(getattr(value, column.key)))
        self.table.blockSignals(blocked)

    def _text(self, row: int, col: int) -> str:
        item = self.table.item(row, col)
        return item.text() if item is not None else ""

    def values(self) -> list[RowValues]:
        """Isi tabel saat ini, apa adanya (tanpa strip), satu ``RowValues`` per baris."""
        result = []
        for row in range(self.table.rowCount()):
            cells = {column.key: self._text(row, col) for col, column in enumerate(self._columns)}
            result.append(RowValues(closing=cells.get("closing", ""), extra=cells.get("extra", ""),
                                    lyric=cells.get("lyric", "")))
        return result

    # -- slots ---------------------------------------------------------------
    def _show_error(self, message: str) -> None:
        self.error.setText(message)
        self.error.setVisible(bool(message))

    def _reset(self) -> None:
        self._fill(self._defaults)
        self._show_error("")

    def _accept(self) -> None:
        self.ok_btn.setFocus()                        # editor sel yang masih terbuka menyimpan isinya dulu
        try:
            check_row_values(self._jutsu, self._targets, self.values())
        except RowValueError as exc:
            self._show_error(str(exc))
            col = next((i for i, c in enumerate(self._columns) if c.key == exc.key), 0)
            self.table.setCurrentCell(exc.row, col)   # sorot sel yang kosong
            self.table.setFocus()
            return
        except JutsuError as exc:
            self._show_error(str(exc))
            return
        self.accept()

    # -- ukuran --------------------------------------------------------------
    def setVisible(self, visible: bool) -> None:
        # Tinggi awal mengikuti jumlah baris, dibatasi agar tidak melebihi layar (sisanya di-scroll).
        if visible and not self._sized:
            self._sized = True
            screen = self.screen() or QGuiApplication.primaryScreen()
            avail = screen.availableGeometry()
            wanted = 230 + self.ROW_HEIGHT * len(self._targets)
            height = max(self.MIN_HEIGHT, min(wanted, int(avail.height() * 0.8)))
            self.resize(min(self.DEFAULT_WIDTH, int(avail.width() * 0.92)), height)
        super().setVisible(visible)
