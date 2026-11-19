"""Error dan pesan untuk operasi Jutsu.

Semua kegagalan yang disebabkan input pengguna / isi script dilaporkan lewat ``JutsuError``.
Pesan di sini sama dengan pesan di aplikasi lama (QMessageBox.critical), supaya perilakunya identik.
"""
from __future__ import annotations


class JutsuError(Exception):
    """Operasi Jutsu tidak bisa dijalankan. ``str(error)`` adalah pesan siap tampil ke pengguna."""


# Pesan bawaan aplikasi lama ---------------------------------------------------------------------
MSG_POSITION_NOT_FOUND = "Position not found!"
MSG_NOT_PHRASE_START = "Position must be start with 'phrase_start'!"
MSG_CHOOSE_CORRECT_PART = "Make sure you choose the correct part of the phrase!"      # khusus Lyric Color (method 1)
MSG_KAN2ROM_LENGTH = "The syllable of the lyrics and the kanji lyrics must be the same length!"
MSG_JUTSU_CHANGED = "This Jutsu was changed in the main editor. The list has been refreshed - edit it again."
MSG_JUTSU_EMPTY = "The Jutsu is empty. Write at least one event line."
