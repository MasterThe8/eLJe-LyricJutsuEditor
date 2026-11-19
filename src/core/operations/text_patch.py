"""Selisih minimal antara teks lama dan teks baru.

Dipakai UI untuk menerapkan hasil Jutsu ke editor tanpa mengganti SELURUH dokumen: hanya bagian yang
berubah yang diganti, lewat edit block QTextCursor. Dengan begitu riwayat Undo/Redo editor (Ctrl+Z / Ctrl+Y)
tetap utuh — ``setPlainText`` justru menghapus riwayat itu.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextPatch:
    """Ganti ``old[start:end]`` dengan ``replacement``. Offset dalam karakter (code point) Python."""

    start: int
    end: int
    replacement: str

    @property
    def is_empty(self) -> bool:
        """True bila tidak ada yang berubah."""
        return self.start == self.end and self.replacement == ""

    def apply(self, old: str) -> str:
        return old[:self.start] + self.replacement + old[self.end:]


def make_patch(old: str, new: str) -> TextPatch:
    """Patch terkecil (awalan dan akhiran yang sama dibuang) sehingga ``make_patch(old, new).apply(old) == new``."""
    limit = min(len(old), len(new))

    start = 0
    while start < limit and old[start] == new[start]:
        start += 1

    # Akhiran tidak boleh menjangkau awalan yang sudah dihitung
    tail = 0
    while tail < limit - start and old[len(old) - 1 - tail] == new[len(new) - 1 - tail]:
        tail += 1

    return TextPatch(start=start, end=len(old) - tail, replacement=new[start:len(new) - tail])
