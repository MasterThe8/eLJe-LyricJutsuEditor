"""Parser lirik — ekstraksi dan manipulasi data lirik dari baris-baris event.

Modul ini menyediakan fungsi-fungsi level tinggi untuk menganalisis dan
memanipulasi konten lirik yang tersimpan di event .chart.

Fungsi-fungsi ini melengkapi ``core.chart.events`` (yang berfokus pada
parsing baris event tunggal) dengan logika yang lebih spesifik pada lirik:
  - Mengelompokkan event per phrase (phrase_start → phrase_end).
  - Mengekstrak teks lirik bersih (tanpa tag markup).
  - Menghitung statistik lirik.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from core.chart.events import ChartEvent, parse_events_text


# ─────────────────────────────────────────────────────────────────────────────
#  Data class untuk satu phrase lirik
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LyricPhrase:
    """Satu phrase lirik, dari ``phrase_start`` sampai ``phrase_end``.

    Attributes:
        start_pos:  Posisi tick ``phrase_start``.
        end_pos:    Posisi tick ``phrase_end`` (None jika belum ditemukan).
        syllables:  List ChartEvent yang bertipe ``lyric`` di dalam phrase ini.
    """

    start_pos: int = 0
    end_pos: int | None = None
    syllables: list[ChartEvent] = field(default_factory=list)

    @property
    def text(self) -> str:
        """Gabungkan semua suku kata menjadi teks lirik utuh.

        Suku kata yang diakhiri ``-`` disambung tanpa spasi.
        """
        result = ""
        for syl in self.syllables:
            value = syl.value
            if result and not result.endswith("-"):
                result += " "
            result += value
        return result.strip()

    @property
    def plain_text(self) -> str:
        """Teks lirik tanpa tag markup (``<b>``, ``<color=...>``, dll)."""
        return strip_tags(self.text)


# ─────────────────────────────────────────────────────────────────────────────
#  Tag stripping
# ─────────────────────────────────────────────────────────────────────────────
_TAG_RE = re.compile(r"</?[^>]+>")


def strip_tags(text: str) -> str:
    """Hapus semua tag markup dari teks (``<b>``, ``<color=...>``, dll)."""
    return _TAG_RE.sub("", text)


# ─────────────────────────────────────────────────────────────────────────────
#  Grouping event menjadi phrase
# ─────────────────────────────────────────────────────────────────────────────

def group_into_phrases(events_text: str) -> list[LyricPhrase]:
    """Kelompokkan event body text menjadi list LyricPhrase.

    Setiap ``phrase_start`` memulai phrase baru, ``phrase_end`` menutupnya.
    Event ``lyric`` di antaranya dikumpulkan sebagai suku kata.
    """
    events = parse_events_text(events_text)
    phrases: list[LyricPhrase] = []
    current: LyricPhrase | None = None

    for ev in events:
        if ev.is_phrase_start:
            # Simpan phrase sebelumnya jika ada
            if current is not None:
                phrases.append(current)
            current = LyricPhrase(start_pos=ev.position)

        elif ev.is_phrase_end:
            if current is not None:
                current.end_pos = ev.position
                phrases.append(current)
                current = None

        elif ev.is_lyric:
            if current is not None:
                current.syllables.append(ev)

    # Phrase terakhir yang belum ditutup phrase_end
    if current is not None:
        phrases.append(current)

    return phrases


# ─────────────────────────────────────────────────────────────────────────────
#  Statistik
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LyricStats:
    """Statistik ringkas dari konten lirik."""

    total_events: int = 0
    total_lyrics: int = 0
    total_phrases: int = 0
    total_sections: int = 0


def compute_stats(events_text: str) -> LyricStats:
    """Hitung statistik dari teks event body."""
    events = parse_events_text(events_text)
    stats = LyricStats(
        total_events=len(events),
        total_lyrics=sum(1 for e in events if e.is_lyric),
        total_phrases=sum(1 for e in events if e.is_phrase_start),
        total_sections=sum(1 for e in events if e.is_section),
    )
    return stats
