"""Dasar dialog Jutsu berbasis warna."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QLabel, QLineEdit, QRadioButton, QVBoxLayout

from core.operations.color_builders import WHITE, normalize_color
from ui.dialogs.operations.base import EventRow, JutsuDialog, note_row
from ui.widgets.color_field import ColorField
from ui.widgets.common import divider, field_label

DEFAULT_JUTSU_COLOR = "#FCA101"          # warna bawaan di dialog asli


# ─────────────────────────────────────────────────────────────────────────────
#  Lyric Color (method 1 & 2) dan Kan2Rom — satu kelas, dua flag
# ─────────────────────────────────────────────────────────────────────────────
class ColorJutsuDialog(JutsuDialog):
    """Kolom kiri: seluruh isian (Position, [Kanji lyric], Color, [Next phrase + Next lyric]).
    Kolom kanan: hanya "Events to insert".

    with_options=False → method 1 (skrip tetap, lihat ``_method1_rows``).
    with_options=True  → method 2 / Kan2Rom (pola grup per suku kata, lihat ``_group_rows``).
    """
    OPTIONS = ["Default (Hide Next Phrase)", "Show Next Phrase", "Add Next Lyric"]
    EVENT_ROWS = 12         # method 2 / Kan2Rom: 2 grup × 5 baris + 1 catatan (Hide / Add Next Lyric)

    def __init__(self, title: str, subtitle: str, icon_name: str, parent=None,
                 with_options: bool = True, with_kanji: bool = False):
        super().__init__(title, subtitle, icon_name, parent)
        self._with_options, self._with_kanji = with_options, with_kanji
        self._option = 0

        # ── kiri: isian lirik ──
        if with_kanji:
            self.kanji = QLineEdit()
            self.kanji.setPlaceholderText("日本語の歌詞…")
            self.form.addLayout(self._field(QLabel("Kanji lyric"), self.kanji))
            self.kanji.textChanged.connect(self._refresh)

        self.color_field = ColorField(DEFAULT_JUTSU_COLOR)
        self.color_hint = field_label("Default color: #FCA101", "fieldHint")
        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(self.color_field)
        row.addWidget(self.color_hint, 1)
        col = QVBoxLayout()
        col.setSpacing(5)
        col.addWidget(field_label("Color"))
        col.addLayout(row)
        self.form.addLayout(col)
        self.color_field.changed.connect(self._on_color)

        # ── kiri: perilaku next phrase (dulu di kolom kanan, di bawah ilustrasi) ──
        if with_options:
            self.form.addSpacing(2)
            self.form.addWidget(divider())
            self.form.addWidget(field_label("Next phrase"))
            self.radios: list[QRadioButton] = []
            group = QButtonGroup(self)
            for i, name in enumerate(self.OPTIONS):
                rb = QRadioButton(name)
                rb.setCursor(Qt.CursorShape.PointingHandCursor)
                group.addButton(rb, i)
                self.radios.append(rb)
                self.form.addWidget(rb)
                rb.toggled.connect(lambda on, i=i: self._set_option(i) if on else None)
            self.radios[0].setChecked(True)

            self.next_lyric = QLineEdit()
            self.next_lyric.setPlaceholderText("Lyric shown as the next phrase…")
            self.next_label = QLabel("Next lyric")
            self.form.addLayout(self._field(self.next_label, self.next_lyric))
            self.next_lyric.textChanged.connect(self._refresh)

        # ── kanan: "Events to insert" dibuat oleh basis ──
        self._finish()
        self._ready = True
        self._on_color()

    def _on_color(self, *_args) -> None:
        if self._ready:
            self.color_hint.setText("Default color" if self.color_field.color() == DEFAULT_JUTSU_COLOR.upper()
                                    else "Custom color")
            self._refresh()

    def _set_option(self, index: int) -> None:
        self._option = index
        self._refresh()

    def _refresh(self, *_args) -> None:
        if not self._ready:                              # dipanggil dini oleh basis
            return
        if self._with_options:
            self._set_pair_enabled(self.next_label, self.next_lyric, self._option == 2)
        super()._refresh()

    # ── "Events to insert" ──────────────────────────────────────────────────
    def _events_rows(self) -> list[EventRow]:
        return self._group_rows() if self._with_options else self._method1_rows()

    def _method1_rows(self) -> list[EventRow]:
        """Lyric Color method 1: skrip tetap (turunan ``apply_lyric_color_method1``).

        Seluruh lirik ditulis putih lebih dulu, lalu suku kata pertama membuka tag warna dan suku kata terakhir
        menutupnya."""
        pos = self._pos
        hex_value = normalize_color(self.color_field.color())
        return [
            (pos(0), "phrase_start", ""),
            (pos(10), "lyric", "{LYRIC}"),
            (pos(11), "phrase_start", ""),
            (pos(12), "lyric", "{HIDDEN/FAKE LYRIC}"),
            (pos(13), "phrase_start", ""),
            (pos(14), "lyric", f"<color={WHITE}><color={hex_value}>L-"),
            (pos(20), "lyric", "y-"),
            (pos(30), "lyric", "r-"),
            (pos(40), "lyric", "i-"),
            (pos(50), "lyric", "c</color></color>"),
        ]

    def _group_rows(self) -> list[EventRow]:
        """Lyric Color method 2 / Kan2Rom: satu grup event per suku kata (turunan ``cc_hide`` / ``cc_nohide`` /
        ``cc_addnext`` + ``add_next_lyric`` di ``core/operations/color_builders.py``).

        Grup pertama jatuh di tick suku kata pertama (N), grup kedua di tick suku kata berikutnya (M), dan
        seterusnya untuk setiap suku kata. Teks berwarna bertambah satu suku kata tiap grup; sisa lirik
        ditempel putih (dari phrase itu sendiri; untuk Kan2Rom dari teks kanji). Grup terakhir tidak punya
        bagian putih."""
        hex_value = normalize_color(self.color_field.color())
        closing = self._lyric["closing_lyric"]
        rest = "{REST OF KANJI}" if self._with_kanji else "{REST}"
        if self._option == 0:                                    # Default (Hide Next Phrase)
            middle = self._lyric["hidden_lyric"]
        elif self._option == 2:                                  # Add Next Lyric
            middle = self.next_lyric.text() or "{NEXT LYRIC}"
        else:                                                    # Show Next Phrase → tanpa baris tengah
            middle = None

        rows: list[EventRow] = []
        for sym, sofar in (("N", "{SYL 1}"), ("M", "{SYL 1}{SYL 2}")):
            colored = f"<color={hex_value}>{sofar}</color><color={WHITE}>{rest}</color>"
            rows.append((self._pos(0, sym), "lyric", closing))
            rows.append((self._pos(1, sym), "phrase_start", ""))
            if middle is None:
                rows.append((self._pos(2, sym), "lyric", colored))
            else:
                rows += [(self._pos(2, sym), "lyric", middle), (self._pos(3, sym), "phrase_start", ""),
                         (self._pos(4, sym), "lyric", colored)]
        rows.append(note_row("… repeated for every syllable"))
        return rows

    def validate(self) -> str:
        msg = super().validate()
        if msg:
            return msg
        if self._with_kanji and not self.kanji.text().strip():
            return "Kanji lyric must be filled in."
        if self._with_options and self._option == 2 and not self.next_lyric.text().strip():
            return "Next lyric must be filled in."
        return ""

    def collect(self) -> dict:
        data = {"position": int(self.position.text()), "color": self.color_field.color()}
        if self._with_kanji:
            data["kanji"] = self.kanji.text()
        if self._with_options:
            data["option"] = self.OPTIONS[self._option]
            data["next_lyric"] = self.next_lyric.text() if self._option == 2 else ""
        return data
