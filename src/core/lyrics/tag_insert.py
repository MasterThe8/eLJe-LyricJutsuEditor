"""Rencana penyisipan tag lirik pada TEKS script Jutsu (editor PlainText) — murni Python, tanpa GUI.

Editor RichText menerapkan tag sebagai format karakter, sedangkan editor PlainText harus menulis markup literal.
Menulis markup di sembarang posisi mudah merusak script (``76<b></b>8 = E "lyric …"``, atau tag di luar tanda
kutip event), jadi penyisipan dirancang di sini dulu:

* Tag hanya boleh masuk ke NILAI event ``lyric`` (lihat ``core.lyrics.jutsu_model.lyric_value_spans``).
* Seleksi dibungkus ``<tag=arg>…</tag>``; seleksi yang membentang beberapa event dibungkus per event, terpotong
  pada batas nilainya. Tanpa seleksi disisipkan pasangan kosong dan kursor ditaruh di antaranya.
* ``<br>`` tidak punya penutup; ia menggantikan seleksi (seperti Shift+Enter di RichText).
* Ditolak (``TagInsertError``) bila titik sisip berada DI DALAM token tag yang sudah ada (``<b|>``), atau bila
  hasilnya membuat tag tidak seimbang padahal sebelumnya seimbang — nilai seperti itu tampil sebagai teks literal di
  RichText dan efek tagnya hilang.

Semua posisi adalah indeks karakter Python pada teks script. Pemanggil di UI yang mengonversi ke/dari posisi Qt.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from core.lyrics.jutsu_model import lyric_value_spans
from core.lyrics.renderer import tags_are_balanced

_TOKEN_RE = re.compile(r"<[^<>]*>")


class TagInsertError(ValueError):
    """Penyisipan tidak bisa dilakukan; pesannya layak ditampilkan ke pengguna."""


@dataclass(frozen=True, slots=True)
class TagEdit:
    """Ganti ``script[start:end]`` dengan ``text`` (koordinat script ASLI)."""

    start: int
    end: int
    text: str


@dataclass(frozen=True, slots=True)
class TagInsertion:
    """``edits`` berurutan menaik dan tidak tumpang tindih. ``select_start``/``select_end`` memakai koordinat script
    BARU (setelah semua edit): rentang yang sebaiknya dipilih, atau kursor biasa bila keduanya sama."""

    edits: tuple[TagEdit, ...]
    select_start: int
    select_end: int

    def apply(self, script: str) -> str:
        """Hasil script setelah semua edit (untuk tes dan pratinjau)."""
        result = script
        for edit in reversed(self.edits):
            result = result[:edit.start] + edit.text + result[edit.end:]
        return result


def _inside_token(value: str, offset: int) -> bool:
    return any(m.start() < offset < m.end() for m in _TOKEN_RE.finditer(value))


def plan_tag_insertion(script: str, sel_start: int, sel_end: int, tag: str, arg: str | None = None, *,
                       void: bool = False) -> TagInsertion:
    """Rencanakan penyisipan ``<tag[=arg]>…</tag>`` (atau ``<tag>`` bila ``void``) pada seleksi.

    Raises:
        TagInsertError: kursor di luar nilai lirik, di dalam token tag, atau hasilnya tidak seimbang.
    """
    if sel_start > sel_end:
        sel_start, sel_end = sel_end, sel_start
    opening = f"<{tag}>" if arg is None else f"<{tag}={arg}>"
    closing = "" if void else f"</{tag}>"
    spans = lyric_value_spans(script)

    # (awal, akhir, span) bagian seleksi yang ada di dalam nilai lirik.
    targets = []
    if sel_start == sel_end:
        span = next((s for s in spans if s.start <= sel_start <= s.end), None)
        if span is not None:
            targets.append((sel_start, sel_end, span))
    else:
        for span in spans:
            first, last = max(sel_start, span.start), min(sel_end, span.end)
            if first < last:
                targets.append((first, last, span))
        if void:
            targets = targets[:1]                                # <br> menggantikan seleksi di satu tempat saja
    if not targets:
        raise TagInsertError("Place the cursor inside a lyric value (the text after “lyric ”) to insert a tag.")

    edits: list[TagEdit] = []
    inner_ranges: list[tuple[int, int]] = []                     # rentang isi, koordinat ASLI + geser kumulatif
    shift = 0
    for first, last, span in targets:
        value = script[span.start:span.end]
        rel_first, rel_last = first - span.start, last - span.start
        if _inside_token(value, rel_first) or _inside_token(value, rel_last):
            raise TagInsertError("The cursor or selection is inside an existing tag. Move it outside the < > markup.")

        inner = "" if void else script[first:last]
        replacement = opening + inner + closing
        separator = " " if span.needs_separator else ""
        edits.append(TagEdit(first, last, separator + replacement))

        new_value = value[:rel_first] + replacement + value[rel_last:]
        if tags_are_balanced(value) and not tags_are_balanced(new_value):
            raise TagInsertError("The selection cuts across other tags. Select text that fully contains "
                                 "(or is fully inside) the tags it overlaps.")

        inner_start = first + shift + len(separator) + len(opening)
        inner_ranges.append((inner_start, inner_start + len(inner)))
        shift += len(separator) + len(replacement) - (last - first)

    if void:
        end = inner_ranges[0][0]
        return TagInsertion(tuple(edits), end, end)
    return TagInsertion(tuple(edits), inner_ranges[0][0], inner_ranges[-1][1])
