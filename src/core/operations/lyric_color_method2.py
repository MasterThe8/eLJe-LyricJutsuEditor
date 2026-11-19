"""Lyric Color no Jutsu (method 2) — dulu ``CCJutsu.mainCCjutsu``.

Mewarnai lirik satu phrase suku kata demi suku kata (warna ``color``), sisanya putih.
Lirik putih diambil dari phrase itu sendiri.
"""
from __future__ import annotations

from core.operations.color_builders import assemble_color_script, build_color_groups
from core.operations.script import get_lyric_item, require_phrase_start, select_phrase


def apply_lyric_color_method2(script: str, position: int, *, color: str, option: str, next_lyric: str,
                              closing_lyric: str, hidden_lyric: str) -> str:
    """Kembalikan script baru (teks lengkap). Melempar JutsuError bila posisi/phrase tidak valid.

    option:     salah satu ``NEXT_PHRASE_*`` (perilaku phrase berikutnya).
    next_lyric: dipakai hanya bila option == ``NEXT_PHRASE_ADD``.
    """
    selection = select_phrase(script.splitlines(), position)
    lines = selection.lines
    lyric_items = get_lyric_item(lines)

    require_phrase_start(lines)

    result = build_color_groups(lines, option, color, next_lyric, closing_lyric, hidden_lyric)
    return assemble_color_script(selection, lyric_items, result)
