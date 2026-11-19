"""Jendela Jutsu Editor: semua Jutsu di script editor, ditampilkan sebagai accordion.

Mirip tab Display Lyrics, tetapi HANYA memuat Jutsu (3/5 tick berurutan hasil Add Jutsu, Lyric Color no Jutsu,
dan Kan2Rom no Jutsu). Pemindaian ada di ``core.operations.jutsu_scan``; jendela ini hanya menampilkannya.

Isi tiap Jutsu bisa diedit. Apply meneruskan hasil edit ke ``apply_handler`` (pemilik jendela), yang mengganti baris
Jutsu itu di editor utama lalu mengurutkan script — satu langkah undo di editor utama. Jendela sendiri tidak pernah
menulis ke editor. Daftar ikut diperbarui saat teks editor berubah; edit yang belum di-Apply tidak hilang karenanya.

Font editor RichText dan PlainText di tiap Jutsu mengikuti jendela utama (RichText → Display Lyrics, PlainText →
PlainText Lyrics). Pemilik mendorongnya lewat ``set_editor_fonts`` saat jendela dibuat dan tiap font editor utama berubah.
"""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel

from core.operations.errors import MSG_JUTSU_CHANGED
from core.operations.jutsu_scan import JutsuBlock, find_jutsu_blocks
from ui.dialogs.base import BaseDialog
from ui.theme import theme_events
from ui.widgets.common import make_button, soft_wrap
from ui.widgets.jutsu_accordion import JutsuAccordionList

REFRESH_DELAY_MS = 250       # jeda setelah ketikan terakhir sebelum daftar dipindai ulang

EMPTY_TEXT = (
    "No Jutsu found in the current script.\n\n"
    "A Jutsu is 3 or 5 lines with consecutive tick values."
)


class JutsuEditorWindow(BaseDialog):
    """Non-modal. ``script_provider`` mengembalikan teks script saat ini (mis. ``plainTextEdit.toPlainText``).

    Pemilik jendela menghubungkan ``textChanged`` editor ke ``schedule_refresh`` agar daftar selalu terkini.
    """

    # Dipasang pemilik jendela: handler(block, teks_edit) -> "" bila berhasil, atau pesan error. Pesan error
    # ditampilkan di item itu dan isiannya dibiarkan (seperti dialog Jutsu lain).
    apply_handler: Callable[[JutsuBlock, str], str] | None = None

    def __init__(self, script_provider: Callable[[], str], parent=None):
        super().__init__("Jutsu Editor", "Every Jutsu in the script. Expand one to see and edit its lines.",
                         "jutsu_editor", parent, modal=False)
        self.resize(560, 680)
        self.setMinimumSize(800, 360)
        self._script_provider = script_provider
        self._last_script: str | None = None            # None → pindai ulang pada refresh berikutnya
        self._blocks: list[JutsuBlock] | None = None    # hasil pemindaian yang sedang tampil; None → bangun ulang

        self.list = JutsuAccordionList()
        self.list.apply_requested.connect(self._on_apply_requested)
        self.body.addWidget(self.list, 1)

        self.empty = QLabel(EMPTY_TEXT)
        self.empty.setObjectName("emptyText")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        soft_wrap(self.empty)
        self.body.addWidget(self.empty, 1)

        self.count = QLabel("")
        self.count.setObjectName("statusNote")
        self.expand_btn = make_button("Expand all", "ghost", "chevron_down")
        self.collapse_btn = make_button("Collapse all", "ghost", "chevron_up")
        self.close_btn = make_button("Close", "ghost")
        self.footer.addWidget(self.count)
        self.footer.addStretch(1)
        self.footer.addWidget(self.expand_btn)
        self.footer.addWidget(self.collapse_btn)
        self.footer.addWidget(self.close_btn)

        self.expand_btn.clicked.connect(lambda: self.list.set_all_expanded(True))
        self.collapse_btn.clicked.connect(lambda: self.list.set_all_expanded(False))
        self.close_btn.clicked.connect(self.close)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(REFRESH_DELAY_MS)
        self._timer.timeout.connect(self.refresh)
        theme_events.changed.connect(self._on_theme_changed)

        self._show_results(0)

    # ── font ────────────────────────────────────────────────────────────────
    def set_editor_fonts(self, plain_font: QFont, rich_font: QFont) -> None:
        """Samakan font editor dengan jendela utama.

        ``plain_font``: font tab PlainText Lyrics → dipakai editor "Jutsu Script".
        ``rich_font``: font tab Display Lyrics → dipakai editor "RichText Lyrics".
        Berlaku juga untuk item yang sudah terbuka dan untuk daftar yang dibangun ulang setelahnya.
        """
        self.list.set_editor_fonts(plain_font, rich_font)

    # ── pembaruan daftar ────────────────────────────────────────────────────
    def schedule_refresh(self) -> None:
        """Dipanggil tiap teks editor berubah. Tidak melakukan apa-apa saat jendela tersembunyi."""
        if self.isVisible():
            self._timer.start()

    def refresh(self, force: bool = False) -> None:
        """Pindai script dan bangun ulang daftar. Item yang sedang terbuka tetap terbuka."""
        script = self._script_provider()
        if not force and script == self._last_script:
            return
        self._last_script = script
        if force:
            self._blocks = None
        blocks = find_jutsu_blocks(script)
        if blocks == self._blocks:                      # mis. mengetik di baris biasa: daftar sama → jangan bangun ulang
            return
        self._blocks = blocks
        self.list.set_blocks(blocks, self.list.expanded_keys(), self.list.drafts())
        self._show_results(len(blocks))

    # ── Apply ───────────────────────────────────────────────────────────────
    def _on_apply_requested(self, widget, text: str) -> None:
        """Get line (hasil scan) → terapkan perubahan → sisipkan ke script → sorting: dikerjakan ``apply_handler``."""
        if self.apply_handler is None:
            widget.show_error("Editing is not available here.")
            return
        error = self.apply_handler(widget.block, text)
        if error:
            widget.show_error(error)
            if error == MSG_JUTSU_CHANGED:               # daftar basi: sinkronkan. Error lain: biarkan item apa adanya
                QTimer.singleShot(0, self.refresh)
            return
        widget.revert()                                  # bersih bila script ternyata tidak berubah (tidak ada refresh)
        QTimer.singleShot(0, self.refresh)               # tunda: daftar dibangun ulang di luar slot tombol ini

    def _show_results(self, n: int) -> None:
        self.list.setVisible(n > 0)
        self.empty.setVisible(n == 0)
        self.expand_btn.setEnabled(n > 0)
        self.collapse_btn.setEnabled(n > 0)
        self.count.setText("No Jutsu" if n == 0 else f"{n} Jutsu found")

    # ── event ───────────────────────────────────────────────────────────────
    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh()

    def _on_theme_changed(self, _theme_id: str = "") -> None:
        """Judul memuat warna tema (placeholder) dan ikon item adalah gambar statis → bangun ulang."""
        self._last_script = None
        self._blocks = None
        if self.isVisible():
            self.refresh()
