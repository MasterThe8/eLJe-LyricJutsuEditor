"""Model data dokumen .chart — menyimpan semua section hasil parsing.

ChartDocument menjadi single source of truth untuk isi file .chart
yang sedang dibuka. Tidak mengandung dependensi GUI apapun.

Modul ini menggantikan class GlobalText lama yang menyimpan raw string
di variabel global (main.py:19-23 dan data/data.py:12-86).

Selain section yang sudah dipisah, dokumen menyimpan ``raw_text`` asli dan
posisi body ``[Events]``. Saat save, writer hanya mengganti bagian body itu;
section lain (termasuk section yang tidak dikenal, urutan, spasi, dan line
ending) tetap apa adanya. Ini yang membuat file asli tidak "dirombak" hanya
karena dibuka lalu disimpan.
"""
from __future__ import annotations

import codecs
import re
from dataclasses import dataclass
from typing import Optional

from core.chart.encoding import pretty_name


# ─────────────────────────────────────────────────────────────────────────────
#  Daftar section instrumen yang dikenal dalam format .chart
# ─────────────────────────────────────────────────────────────────────────────
DIFFICULTIES = ("Expert", "Hard", "Medium", "Easy")

INSTRUMENTS = (
    "Single",
    "DoubleGuitar",
    "DoubleBass",
    "DoubleRhythm",
    "Keyboard",
    "Drums",
    "GHLGuitar",
    "GHLBass",
    "GHLRhythm",
    "GHLCoop",
)


@dataclass
class ChartDocument:
    """Menyimpan seluruh isi file .chart yang sudah di-parse per section.

    Attributes:
        song:          Isi mentah section ``[Song]``  (termasuk header dan braces).
        sync_track:    Isi mentah section ``[SyncTrack]``.
        events_header: Header ``[Events]`` + brace buka, dengan placeholder ``songrex``
                       di tengahnya — dipakai sebagai fallback bila raw_text tidak ada.
        events_body:   Konten event mentah (tanpa braces), yang akan ditampilkan
                       di editor PlainText.
        note_sections: Gabungan seluruh section instrumen/difficulty
                       (ExpertSingle, HardDrums, dst).
        file_path:     Path file asal (``None`` jika belum pernah disimpan).
        encoding:      Codec Python yang dipakai untuk decode/encode file.
        bom:           BOM asli file (``b""`` jika tidak ada).
        raw_text:      Seluruh isi file setelah decode, sebelum diubah.
        raw_bytes:     Byte asli file (tanpa diubah).
        events_body_start/end:
                       Rentang karakter body ``[Events]`` di dalam ``raw_text``
                       (di antara ``{`` dan ``}``).
        newline:       Gaya line ending dominan file (``"\\n"``, ``"\\r\\n"``, ``"\\r"``).
    """

    song: str = ""
    sync_track: str = ""
    events_header: str = ""
    events_body: str = ""
    note_sections: str = ""
    file_path: Optional[str] = None
    encoding: str = "utf-8"
    bom: bytes = b""

    raw_text: str = ""
    raw_bytes: bytes = b""
    events_body_start: int = -1
    events_body_end: int = -1
    newline: str = "\n"

    encoding_confidence: float = 1.0
    encoding_warning: Optional[str] = None

    # ── placeholder yang dipakai di events_header ────────────────────────
    PLACEHOLDER = "songrex"

    # ── query helpers ────────────────────────────────────────────────────
    @property
    def has_content(self) -> bool:
        """True jika dokumen sudah terisi (pernah di-parse)."""
        return bool(self.raw_text or self.song or self.events_body)

    @property
    def encoding_label(self) -> str:
        """Nama encoding siap tampil, mis. ``UTF-8`` / ``SHIFT_JIS`` / ``UTF-8 BOM``."""
        if self.bom == codecs.BOM_UTF8:
            return "UTF-8 BOM"
        label = pretty_name(self.encoding)
        return f"{label} BOM" if self.bom else label

    @property
    def has_events_span(self) -> bool:
        """True jika posisi body ``[Events]`` valid dan bisa di-splice."""
        return (
            bool(self.raw_text)
            and 0 <= self.events_body_start <= self.events_body_end <= len(self.raw_text)
        )

    # ── assembly ─────────────────────────────────────────────────────────
    def assembled_text(self, editor_text: str) -> str:
        """Gabungkan dokumen menjadi teks .chart utuh, siap tulis ke disk.

        Jika ``raw_text`` tersedia, hanya body ``[Events]`` yang diganti.
        Semua section lain dipertahankan persis seperti file asli.
        Jika tidak, fallback ke perilaku lama (Song + SyncTrack + Events + Notes).
        """
        if self.has_events_span:
            body = self._framed_events_body(editor_text)
            return (
                self.raw_text[: self.events_body_start]
                + body
                + self.raw_text[self.events_body_end :]
            )

        # ── fallback untuk dokumen yang dibuat manual / file tanpa raw_text ──
        content = _normalise_newlines(editor_text).replace(
            "\n", self.newline + "  "
        )
        indented = "  " + content
        events_full = self.events_header.replace(self.PLACEHOLDER, indented)
        return self.song + self.sync_track + events_full + self.note_sections

    def _framed_events_body(self, editor_text: str) -> str:
        """Susun ulang body ``[Events]`` dengan framing/indentasi asli."""
        original = self.raw_text[self.events_body_start : self.events_body_end]

        # Fast path: user tidak mengubah apa pun → kembalikan byte-body asli
        # persis, termasuk blank line/indentasi yang tidak konsisten.
        if _normalise_newlines(editor_text) == self.events_body:
            return original

        stripped = original.strip()

        if not stripped:
            # Body kosong: pakai framing standar.
            indent = "  "
            lead = self.newline + indent
            trail = self.newline
        else:
            first = len(original) - len(original.lstrip())
            last = len(original.rstrip())
            lead = original[:first]
            trail = original[last:]

            content_region = original[first:last]
            match = re.search(r"(?m)^([ \t]+)\S", content_region)
            indent = match.group(1) if match else "  "

        content = _normalise_newlines(editor_text)
        if content:
            lines = content.split("\n")
            framed = [lines[0]]
            for line in lines[1:]:
                framed.append(self.newline)
                if line:
                    framed.append(indent)
                framed.append(line)
            content = "".join(framed)

        return lead + content + trail


def _normalise_newlines(text: str) -> str:
    """Ubah CRLF/CR menjadi LF agar aman sebelum digabung ulang."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


# ─────────────────────────────────────────────────────────────────────────────
#  Helper line ending
# ─────────────────────────────────────────────────────────────────────────────

def detect_newline(text: str) -> str:
    """Deteksi gaya line ending dominan pada *text*."""
    crlf = text.count("\r\n")
    lf = text.count("\n") - crlf
    cr = text.count("\r") - crlf
    if crlf == 0 and lf == 0 and cr == 0:
        return "\n"
    if crlf >= lf and crlf >= cr:
        return "\r\n"
    if cr >= lf:
        return "\r"
    return "\n"
