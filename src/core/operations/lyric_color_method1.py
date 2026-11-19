"""Lyric Color no Jutsu (method 1) — dulu ``LCJutsu.mainLCJutsu``.

Seluruh phrase ditampilkan putih; lirik pertama membuka warna (``<color=HEX>``) dan lirik terakhir
menutupnya (``</color></color>``). Event sebelum lirik pertama ditambahkan (posisi -4 s/d -1) untuk
menampilkan phrase utuh dan menyembunyikan phrase berikutnya.
"""
from __future__ import annotations

from core.operations.color_builders import WHITE, normalize_color
from core.operations.errors import JutsuError, MSG_CHOOSE_CORRECT_PART
from core.operations.script import (
    get_lyric_item,
    insert_and_sort,
    lyric_event,
    phrase_start_event,
    require_phrase_start,
    select_phrase,
    split_lyric,
)


def convert_list_to_string(lyric_items: list[str]) -> str:
    """Gabungkan item lirik jadi satu kalimat: spasi di antara kata, tanpa spasi setelah item berakhiran '-'."""
    result = ""
    for i, item in enumerate(lyric_items):
        if i > 0 and not lyric_items[i - 1].endswith("-"):
            result += " "
        result += item.rstrip("-")
    return result


def find_first_lyric_element(lyric_items: list[str]) -> str | None:
    """Baris lirik pertama (baris yang memuat 'lyric'); baris itu DIHAPUS dari ``lyric_items``."""
    first_lyric_element = None
    for item in lyric_items:
        if "lyric" in item:
            first_lyric_element = item
            lyric_items.remove(item)
            break
    return first_lyric_element


def find_last_lyric_element(lyric_items: list[str]) -> str | None:
    """Baris lirik terakhir (baris yang memuat 'lyric'); baris itu DIHAPUS dari ``lyric_items``."""
    last_lyric_element = None
    for item in reversed(lyric_items):
        if "lyric" in item:
            last_lyric_element = item
            lyric_items.remove(item)
            break
    return last_lyric_element


def apply_lyric_color(lyric: str, pos: int, syllable: str, color: str | None, hidden_lyric: str) -> list[str]:
    """5 baris pembuka: phrase utuh (pos-4), phrase_start, hidden, phrase_start, lirik pertama berwarna (pos)."""
    hex_value = normalize_color(color)

    # (dulu ada dua cabang `if '-' in syllable` / else dengan hasil yang sama persis)
    line1 = lyric_event(int(pos) - 4, lyric)
    line2 = phrase_start_event(int(pos) - 3)
    line3 = lyric_event(int(pos) - 2, hidden_lyric)
    line4 = phrase_start_event(int(pos) - 1)
    line5 = lyric_event(int(pos), "<color=" + WHITE + "><color=" + hex_value + ">" + syllable)

    return [line1, line2, line3, line4, line5]


def apply_lyric_close(pos: int, syllable: str) -> str:
    """Baris lirik terakhir + penutup kedua tag warna."""
    return lyric_event(int(pos), syllable + "</color></color>")


def apply_lyric_color_method1(script: str, position: int, *, color: str, hidden_lyric: str) -> str:
    """Kembalikan script baru (teks lengkap). Melempar JutsuError bila posisi/phrase tidak valid."""
    selection = select_phrase(script.splitlines(), position)
    lines = selection.lines
    lyric_items = get_lyric_item(lines)

    require_phrase_start(lines)

    lyric_items = convert_list_to_string(lyric_items)
    first_lyric = find_first_lyric_element(lines)
    last_lyric = find_last_lyric_element(lines)

    # Phrase yang hanya punya satu lirik (atau bentuk baris lirik tak dikenal) → tidak ada "bagian yang benar"
    if first_lyric is None or last_lyric is None:
        raise JutsuError(MSG_CHOOSE_CORRECT_PART)
    try:
        f_pos, f_value = split_lyric(first_lyric)
        l_pos, l_value = split_lyric(last_lyric)
    except (IndexError, ValueError):
        raise JutsuError(MSG_CHOOSE_CORRECT_PART) from None

    first_phrase = apply_lyric_color(lyric_items, f_pos, f_value, color, hidden_lyric)
    last_phrase = apply_lyric_close(l_pos, l_value)

    lines = insert_and_sort(lines, first_phrase)
    lines = insert_and_sort(lines, last_phrase)

    # Urutan gabung (posisi sama): baris di luar phrase → baris phrase → section
    final_result = insert_and_sort(selection.temp_value, lines)
    final_result = insert_and_sort(final_result, selection.temp_section)
    return "\n".join(final_result)
