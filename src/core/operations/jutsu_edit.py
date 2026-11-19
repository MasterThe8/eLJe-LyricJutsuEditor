"""Jutsu Editor — menerapkan hasil edit satu Jutsu ke script.

Alurnya sama dengan Jutsu lain:  ambil baris (hasil ``find_jutsu_blocks``)  →  terapkan perubahan  →
sisipkan ke script  →  sorting.

* Baris Jutsu lama diganti DI TEMPATNYA oleh baris hasil edit.
* Seluruh script lalu diurutkan menurut posisi (tick) dengan sort STABIL (``sort_script_by_position``), sama seperti
  Add Jutsu / Lyric Color / Kan2Rom. Karena stabil, baris yang tick-nya sama tetap berurutan seperti di editor.

Fungsi ini hanya MENYUSUN teks baru; menaruhnya di editor (satu langkah undo) dilakukan lapisan UI lewat ``make_patch``.
Murni Python, tanpa import GUI.
"""
from __future__ import annotations

from core.chart.events import parse_event_line
from core.operations.errors import JutsuError, MSG_JUTSU_CHANGED, MSG_JUTSU_EMPTY
from core.operations.jutsu_scan import JutsuBlock, find_jutsu_blocks
from core.operations.script import sort_script_by_position, validate_events


def _locate(script: str, lines: list[str], block: JutsuBlock) -> tuple[int, int]:
    """Rentang baris ``[start, end)`` milik ``block`` di script SAAT INI.

    Jalur cepat: baris di posisi lama masih sama persis. Bila tidak (script bergeser, mis. baris ditambah di atasnya),
    cari Jutsu yang isinya identik lewat pemindaian ulang dan ambil yang terdekat. Tidak ketemu → JutsuError.
    """
    start, end = block.start_line, block.end_line
    if tuple(lines[start:end]) == block.lines:
        return start, end
    same = [b for b in find_jutsu_blocks(script) if b.lines == block.lines]
    if not same:
        raise JutsuError(MSG_JUTSU_CHANGED)
    nearest = min(same, key=lambda b: abs(b.start_line - block.start_line))
    return nearest.start_line, nearest.end_line


def parse_edited_lines(text: str) -> list[str]:
    """Teks hasil edit → daftar baris event. Baris kosong dibuang; spasi di ujung tiap baris dipangkas.

    Melempar JutsuError (menyebut nomor baris DI DALAM Jutsu) bila ada baris yang bukan ``<tick> = E "<nama> ..."``.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise JutsuError(MSG_JUTSU_EMPTY)
    for number, line in enumerate(lines, start=1):
        if parse_event_line(line) is None:
            raise JutsuError(f'Jutsu line {number} is not a valid event: {line!r}')
    return lines


def apply_jutsu_edit(script: str, block: JutsuBlock, new_text: str) -> str:
    """Kembalikan script baru (teks lengkap) setelah ``block`` diganti ``new_text`` lalu script diurutkan.

    Melempar JutsuError bila ``new_text`` kosong / tidak valid, bila Jutsu itu sudah berubah di editor, atau bila
    script punya baris yang bukan event (sama seperti Jutsu lain, karena pengurutan butuh tick di tiap baris).
    """
    new_lines = parse_edited_lines(new_text)

    lines = script.splitlines()
    validate_events(lines)                                  # nomor baris di pesan = nomor baris di editor
    start, end = _locate(script, lines, block)

    merged = lines[:start] + new_lines + lines[end:]        # sisipkan di tempat Jutsu lama
    result = "\n".join(sort_script_by_position(merged))     # sorting
    if script.endswith(("\n", "\r")):                       # jaga newline penutup bila editor memilikinya
        result += "\n"
    return result
