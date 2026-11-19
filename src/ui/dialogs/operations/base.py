"""Kerangka dialog operasi Jutsu. Setiap dialog memancarkan jutsu_requested(dict) saat Apply.

Tata letak dua kolom (lebar & pendek, bukan satu kolom tinggi):

    ┌ header ───────────────────────────────────────────────────────┐
    │  form (self.form, kiri)      │  Events to insert (self.events) │
    │   • Lyric position           │   • baris event yang akan       │
    │   • field milik subclass     │     disisipkan ke editor        │
    ├ footer ───────────────────────────────────────────────────────┤
    │  [pesan error] ·································· [Cancel][Apply]│
    └───────────────────────────────────────────────────────────────┘

Kolom kanan HANYA berisi "Events to insert" (tidak ada lagi ilustrasi Preview). Seluruh isian — termasuk pilihan
perilaku milik subclass — ada di kolom kiri.

Subclass mengisi `self.form`, mengisi `_events_rows()` (baris event yang ditampilkan di kanan), lalu memanggil
`self._finish()` di akhir __init__. Tinggi tampilan event dicadangkan lewat atribut kelas `EVENT_ROWS`.
"""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QRegularExpression, QSize, Qt, Signal
from PySide6.QtGui import QFontMetrics, QGuiApplication, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLayout, QLineEdit, QMessageBox, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from services.defaults import DEFAULT_HIGHLIGHT, DEFAULT_LYRIC
from ui.dialogs.base import BaseDialog
from ui.html_helpers import span
from ui.theme import Theme, mono_font, to_qcolor
from ui.widgets.common import divider, field_label, make_button


# ─────────────────────────────────────────────────────────────────────────────
#  "Events to insert": tampilan baris event berwarna
# ─────────────────────────────────────────────────────────────────────────────
# Satu baris = (posisi, nama_event, teks). Bila nama_event kosong, baris ditampilkan apa adanya sebagai catatan
# (dipakai untuk "…" / keterangan pengulangan), memakai `posisi` sebagai isi teksnya.
EventRow = tuple[str, str, str]


def note_row(text: str) -> EventRow:
    """Baris catatan polos (bukan event), mis. ``… repeated for every syllable``."""
    return (text, "", "")


def events_html(colors: dict, rows: list[EventRow]) -> str:
    """Beberapa baris event berwarna (meniru LyricHighlighter), dalam satu <pre>."""
    note_color = to_qcolor(Theme.FAINT).name()
    lines = []
    for pos, event, text in rows:
        if not event:
            lines.append(span(note_color, pos))
            continue
        value = span(colors["value"], '"') + span(colors["eventname"], event)
        if text:
            value += span(colors["value"], " " + text)
        value += span(colors["value"], '"')
        lines.append(f"{span(colors['position'], pos)} = E {value}")
    return "<pre style='margin:0'>" + "\n".join(lines) + "</pre>"


class EventsView(QScrollArea):
    """Tampilan event: tinggi dicadangkan untuk `rows` baris, lebar mengikuti kolom.

    Baris yang lebih lebar dari kolom TIDAK dipotong dan TIDAK membungkus: muncul scrollbar horizontal di dalam
    kotak ini, sehingga teks lengkap tetap bisa dibaca dan dialog tidak pernah berubah ukuran karena isinya.
    """

    def __init__(self, rows: int = 5, parent=None):
        super().__init__(parent)
        mono = mono_font(11)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.viewport().setAutoFillBackground(False)

        self._label = QLabel()
        self._label.setFont(mono)
        self._label.setTextFormat(Qt.TextFormat.RichText)
        self._label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setWidget(self._label)
        self._label.setAutoFillBackground(False)         # QScrollArea.setWidget menyalakannya; matikan lagi

        # tinggi: `rows` baris + ruang scrollbar horizontal (agar muncul/hilangnya scrollbar tidak menggeser tinggi)
        bar = self.horizontalScrollBar().sizeHint().height()
        self._min_height = QFontMetrics(mono).lineSpacing() * rows + bar + 4
        self.setMinimumHeight(self._min_height)

    def sizeHint(self) -> QSize:                       # jangan biarkan lebar teks mendorong lebar dialog
        return QSize(280, self._min_height)

    def minimumSizeHint(self) -> QSize:
        return QSize(120, self._min_height)

    def set_rows(self, colors: dict, rows: list[EventRow]) -> None:
        self._label.setText(events_html(colors, rows))


# ─────────────────────────────────────────────────────────────────────────────
#  Kerangka dialog Jutsu
# ─────────────────────────────────────────────────────────────────────────────
class JutsuDialog(BaseDialog):
    """Dua kolom (form | Events to insert) + footer berisi pesan error, Cancel, dan Apply."""
    jutsu_requested = Signal(dict)
    _ready = False          # True setelah subclass selesai membangun field-nya

    # Dipasang pemilik dialog: handler(payload) -> "" bila berhasil, atau pesan error. Pesan error
    # ditampilkan dan dialog TETAP terbuka (seperti dialog aslinya), supaya isian tidak hilang.
    apply_handler: Callable[[dict], str] | None = None

    EVENT_ROWS = 5          # tinggi (jumlah baris) yang dicadangkan untuk "Events to insert"; subclass boleh menimpa
    MIN_WIDTH = 700         # batas terkecil yang masih nyaman untuk dua kolom
    DEFAULT_WIDTH = 880     # lebar awal saat dibuka (kolom kanan lebih lebar: baris event cukup panjang)
    SCREEN_FRACTION = 0.92  # dialog tidak pernah melebihi porsi ini dari area layar yang tersedia

    def __init__(self, title: str, subtitle: str, icon_name: str, parent=None):
        super().__init__(title, subtitle, icon_name, parent)
        self.setMinimumWidth(self.MIN_WIDTH)
        self._colors = dict(DEFAULT_HIGHLIGHT)
        self._sized = False

        # ── dua kolom ───────────────────────────────────────────────────────
        self.form = QVBoxLayout()           # kiri: isian
        self.form.setSpacing(12)
        self.side = QVBoxLayout()           # kanan: hanya "Events to insert"
        self.side.setSpacing(8)
        cols = QHBoxLayout()
        cols.setSpacing(22)
        cols.addLayout(self.form, 2)
        cols.addWidget(divider(vertical=True))
        cols.addLayout(self.side, 3)
        self.body.addLayout(cols, 1)

        # ── kanan: hanya "Events to insert" ─────────────────────────────────
        self._lyric = dict(DEFAULT_LYRIC)
        self.events = EventsView(rows=self.EVENT_ROWS)
        box = QFrame()
        box.setObjectName("previewBox")
        bl = QVBoxLayout(box)
        bl.setContentsMargins(14, 10, 14, 10)
        bl.addWidget(self.events)
        self.side.addWidget(field_label("Events to insert (Example)"))
        self.side.addWidget(box, 1)

        # ── kiri: posisi ────────────────────────────────────────────────────
        self.position = QLineEdit()
        self.position.setPlaceholderText("Tick value, e.g. 3072")
        self.position.setValidator(QRegularExpressionValidator(QRegularExpression(r"\d{0,12}")))
        self.position.setClearButtonEnabled(True)
        self.position.setFont(mono_font(11))
        self.position_label = QLabel("Lyric position")
        self.form.addLayout(self._field(self.position_label, self.position,
                                        "Tip: select the position number in the editor before opening this window."))

        # ── footer: error di kiri, tombol di kanan ──────────────────────────
        self.footer.setContentsMargins(22, 12, 22, 12)      # sejajar dengan margin body
        self.error = QLabel("")
        self.error.setObjectName("errorNote")
        self.error.hide()
        self.cancel_btn = make_button("Cancel", "ghost")
        self.apply_btn = make_button("Apply Jutsu", "primary", "check")
        self.apply_btn.setDefault(True)
        self.footer.addWidget(self.error)
        self.footer.addStretch(1)
        self.footer.addWidget(self.cancel_btn)
        self.footer.addWidget(self.apply_btn)

        self.cancel_btn.clicked.connect(self.reject)
        self.apply_btn.clicked.connect(self._apply)
        self.position.textChanged.connect(self._on_position)
        self._on_position("")

    # -- builder helpers -----------------------------------------------------
    def _field(self, label: QLabel, widget: QWidget, hint: str = "") -> QVBoxLayout:
        label.setObjectName("fieldLabel")
        col = QVBoxLayout()
        col.setSpacing(5)
        col.addWidget(label)
        col.addWidget(widget)
        if hint:
            col.addWidget(field_label(hint, "fieldHint", wrap=True))
        return col

    def _finish(self) -> None:
        """Panggil di akhir __init__ subclass: sisa ruang kolom kiri jatuh ke bawah, dan urutan Tab dirapikan.

        Kolom kanan tidak perlu stretch: kotak event sudah mengisi seluruh tinggi kolom."""
        self.form.addStretch(1)
        self._apply_tab_order()

    @classmethod
    def _focusable(cls, layout: QLayout):
        """Widget yang bisa difokuskan di dalam layout, berurutan seperti tampilannya (rekursif)."""
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() is not None:
                if item.widget().focusPolicy() != Qt.FocusPolicy.NoFocus:
                    yield item.widget()
            elif item.layout() is not None:
                yield from cls._focusable(item.layout())

    def _apply_tab_order(self) -> None:
        """Tab: kolom kiri (atas→bawah), lalu kolom kanan, lalu Cancel dan Apply.

        Tanpa ini, urutan mengikuti waktu pembuatan widget: tombol footer (dibuat di basis) menyela di antara
        Position dan field milik subclass."""
        order = [*self._focusable(self.form), *self._focusable(self.side), self.cancel_btn, self.apply_btn]
        for a, b in zip(order, order[1:]):
            QWidget.setTabOrder(a, b)

    @staticmethod
    def _set_pair_enabled(label: QLabel, edit: QWidget, enabled: bool) -> None:
        label.setEnabled(enabled)
        edit.setEnabled(enabled)

    # -- ukuran --------------------------------------------------------------
    def setVisible(self, visible: bool) -> None:
        # Ukuran awal dihitung sekali, tepat sebelum tampil, saat semua teks/pratinjau sudah final.
        if visible and not self._sized:
            self._sized = True
            self._fit_to_screen()
        super().setVisible(visible)

    def _fit_to_screen(self) -> None:
        """Ukuran awal = kebutuhan isi, tapi tidak pernah lebih besar dari layar yang tersedia."""
        lay = self.layout()
        lay.activate()
        screen = self.screen() or QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()
        width = min(max(self.DEFAULT_WIDTH, lay.totalSizeHint().width()), int(avail.width() * self.SCREEN_FRACTION))
        height = min(lay.totalHeightForWidth(width), int(avail.height() * self.SCREEN_FRACTION))
        self.resize(width, height)

    # -- API -----------------------------------------------------------------
    def set_position(self, position: int) -> None:
        self.position.setText(str(position))

    def set_lyric_settings(self, lyric: dict, colors: dict) -> None:
        """Terima closing/hidden lyric dari setting dan warna highlight, lalu gambar ulang "Events to insert"."""
        self._lyric = dict(DEFAULT_LYRIC, **lyric)
        self._colors = dict(DEFAULT_HIGHLIGHT, **colors)
        self._refresh()

    # -- slots ---------------------------------------------------------------
    def _show_error(self, message: str) -> None:
        """Tampilkan / sembunyikan pesan error di footer."""
        self.error.setText(message)
        self.error.setVisible(bool(message))

    def _on_position(self, text: str) -> None:
        self._show_error("")
        self.apply_btn.setEnabled(bool(text))
        self._refresh()

    def _refresh(self, *_args) -> None:
        """Gambar ulang "Events to insert". Subclass yang menimpa ini wajib memanggil ``super()._refresh()``."""
        if self._ready:                                  # dipanggil dini oleh basis saat subclass belum selesai
            self.events.set_rows(self._colors, self._events_rows())

    def _events_rows(self) -> list[EventRow]:
        """Baris event yang akan disisipkan (diisi subclass)."""
        return []

    # Simbol posisi di "Events to insert" → jarak (tick) dari nilai Position: N = Position, M = Position + 100
    POS_SYMBOLS = {"N": 0, "M": 100}

    def _pos(self, offset: int = 0, sym: str = "N") -> str:
        """Teks posisi. Bila Position terisi → angka sungguhan (``N`` = Position, ``M`` = Position + 100, lalu
        ditambah ``offset``); bila kosong → simbol (``N``, ``N+4``, ``M``, ``M+4``)."""
        text = self.position.text()
        if text.isdigit():
            return str(int(text) + self.POS_SYMBOLS[sym] + offset)
        return sym if offset == 0 else f"{sym}+{offset}"

    def collect(self) -> dict:
        raise NotImplementedError

    def validate(self) -> str:
        return "" if self.position.text().isdigit() else "Position must be filled in correctly."

    def _apply(self) -> None:
        msg = self.validate()
        if msg:
            self._show_error(msg)
            return
        payload = self.collect()
        if self.apply_handler is not None:
            error = self.apply_handler(payload)
            if error:
                QMessageBox.critical(self, "Error", error)
                return
        self.jutsu_requested.emit(payload)
        self.accept()
