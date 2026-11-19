"""Dialog Add Jutsu."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QLabel, QLineEdit

from ui.dialogs.operations.base import EventRow, JutsuDialog


# ─────────────────────────────────────────────────────────────────────────────
#  Add Jutsu
# ─────────────────────────────────────────────────────────────────────────────
class AddJutsuDialog(JutsuDialog):
    NAMES = ["No SlideUp Transition", "Hide Next Phrase", "Fake Next Phrase"]
    EVENT_ROWS = 5          # jumlah baris event terbanyak (Hide / Fake Next Phrase)

    def __init__(self, parent=None):
        super().__init__("Add Jutsu", "Insert a lyric that ends the current phrase and starts a new one.",
                         "add", parent)

        # ── kiri: isian ──
        self.combo = QComboBox()
        self.combo.addItems(self.NAMES)
        self.combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.form.addLayout(self._field(QLabel("Jutsu"), self.combo))

        self.lyric = QLineEdit()
        self.lyric.setPlaceholderText("Lyric to insert…")
        self.lyric_label = QLabel("Lyric")
        self.form.addLayout(self._field(self.lyric_label, self.lyric))

        self.fake = QLineEdit()
        self.fake.setPlaceholderText("Text shown as the fake next phrase…")
        self.fake_label = QLabel("Fake lyric")
        self.form.addLayout(self._field(self.fake_label, self.fake))

        # ── kanan: "Events to insert (Example)" dibuat oleh basis; tinggi dicadangkan untuk 5 baris (maksimum), sehingga
        #    mengganti jutsu atau mengetik lirik panjang tidak membuat dialog berubah ukuran.
        self._finish()

        self.combo.currentIndexChanged.connect(self._refresh)
        self.lyric.textChanged.connect(self._refresh)
        self.fake.textChanged.connect(self._refresh)
        self._ready = True
        self._refresh()

    def _refresh(self, *_args) -> None:
        if not self._ready:                              # dipanggil dini oleh basis
            return
        self._set_pair_enabled(self.fake_label, self.fake, self.combo.currentIndex() == 2)
        super()._refresh()

    def _events_rows(self) -> list[EventRow]:
        idx = self.combo.currentIndex()
        pos = self._pos
        lyric = self.lyric.text() or "…"
        rows: list[EventRow] = [(pos(0), "lyric", self._lyric["closing_lyric"]), (pos(1), "phrase_start", "")]
        if idx == 0:
            rows.append((pos(2), "lyric", lyric))
        else:
            middle = self._lyric["hidden_lyric"] if idx == 1 else (self.fake.text() or "…")
            rows += [(pos(2), "lyric", middle), (pos(3), "phrase_start", ""), (pos(4), "lyric", lyric)]
        return rows

    def validate(self) -> str:
        msg = super().validate()
        if msg:
            return msg
        if not self.lyric.text().strip():
            return "Lyric must be filled in."
        if self.combo.currentIndex() == 2 and not self.fake.text().strip():
            return "Fake lyric must be filled in."
        return ""

    def collect(self) -> dict:
        return {"jutsu": self.NAMES[self.combo.currentIndex()], "position": int(self.position.text()),
                "lyric": self.lyric.text(), "fake_lyric": self.fake.text()}
