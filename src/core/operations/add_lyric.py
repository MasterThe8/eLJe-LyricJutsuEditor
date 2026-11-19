"""Add Jutsu — dulu ``AddJutsu.accept`` (Jutsu.py).

Membuat event yang mengakhiri phrase saat ini lalu memulai phrase baru berisi lirik pengguna.
Fungsi ini hanya MEMBUAT teksnya; menempatkannya di editor (mengganti baris kursor) dilakukan lapisan UI.
"""
from __future__ import annotations

from core.operations.errors import JutsuError
from core.operations.script import lyric_event, phrase_start_event

# Nama jutsu di dialog (harus sama dengan AddJutsuDialog.NAMES)
ADD_NO_SLIDEUP = "No SlideUp Transition"
ADD_HIDE_NEXT = "Hide Next Phrase"
ADD_FAKE_NEXT = "Fake Next Phrase"


def build_add_jutsu_text(jutsu: str, position: int, *, lyric: str, fake_lyric: str,
                         closing_lyric: str, hidden_lyric: str) -> str:
    """Teks event hasil Add Jutsu (baris dipisah ``\\n``, tanpa newline di akhir)."""
    if jutsu == ADD_NO_SLIDEUP:
        line1 = lyric_event(position, closing_lyric)
        line2 = phrase_start_event(position + 1)
        line3 = lyric_event(position + 2, lyric)
        return line1 + "\n" + line2 + "\n" + line3

    if jutsu == ADD_HIDE_NEXT:
        line1 = lyric_event(position, closing_lyric)
        line2 = phrase_start_event(position + 1)
        line3 = lyric_event(position + 2, hidden_lyric)
        line4 = phrase_start_event(position + 3)
        line5 = lyric_event(position + 4, lyric)
        return line1 + "\n" + line2 + "\n" + line3 + "\n" + line4 + "\n" + line5

    if jutsu == ADD_FAKE_NEXT:
        line1 = lyric_event(position, closing_lyric)
        line2 = phrase_start_event(position + 1)
        line3 = lyric_event(position + 2, fake_lyric)
        line4 = phrase_start_event(position + 3)
        line5 = lyric_event(position + 4, lyric)
        return line1 + "\n" + line2 + "\n" + line3 + "\n" + line4 + "\n" + line5

    raise JutsuError(f"Unknown jutsu: {jutsu!r}")
