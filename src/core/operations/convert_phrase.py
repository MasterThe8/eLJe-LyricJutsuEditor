"""Kan2Rom no Jutsu — dulu ``CnvrtJutsu.mainCnvrtJutsu``.

Sama seperti Lyric Color (method 2), tetapi sisa lirik putih diambil dari teks kanji yang diketik
pengguna, bukan dari phrase. Jumlah suku kata kanji harus sama dengan jumlah event phrase.
"""
from __future__ import annotations

from core.operations.color_builders import assemble_color_script, build_color_groups
from core.operations.errors import JutsuError, MSG_KAN2ROM_LENGTH
from core.operations.script import require_phrase_start, select_phrase


def get_kanji_items(lyric: str) -> list[str]:
    """Pecah teks kanji menjadi suku kata (dulu ``CnvrtJutsu.get_lyric_item``).

    ``-`` memotong dan menempel ``-`` di akhir suku kata; spasi memotong dan menempel spasi.
    Contoh: ``'日本語 の-歌詞'`` → ``['日本語 ', 'の-', '歌詞']``. Pemisah beruntun tidak menghasilkan item kosong.
    """
    text_string = lyric.strip()

    converted_list = []
    word = ""

    for char in text_string:
        if char == "-":
            if word != "":
                converted_list.append(word + "-")
                word = ""
        elif char == " ":
            if word != "":
                converted_list.append(word + " ")
                word = ""
        else:
            word += char

    if word != "":
        converted_list.append(word)

    return converted_list


def apply_kan2rom(script: str, position: int, *, kanji: str, color: str, option: str, next_lyric: str,
                  closing_lyric: str, hidden_lyric: str) -> str:
    """Kembalikan script baru (teks lengkap). Melempar JutsuError bila posisi/phrase/jumlah suku kata tidak valid."""
    selection = select_phrase(script.splitlines(), position)
    lines = selection.lines
    lyric_items = get_kanji_items(kanji)

    require_phrase_start(lines)

    lines_len = len(lines)
    lyric_len = len(lyric_items) + 1                       # +1 untuk baris phrase_start
    if lines_len != lyric_len:
        raise JutsuError(MSG_KAN2ROM_LENGTH)

    result = build_color_groups(lines, option, color, next_lyric, closing_lyric, hidden_lyric)
    return assemble_color_script(selection, lyric_items, result)
