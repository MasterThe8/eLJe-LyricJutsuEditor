"""Parser file .chart — membaca bytes dan memecahnya menjadi ChartDocument.

Logika dimigrasi dari:
  - ``main.py`` method ``read_chart()`` (baris 1082-1122)
  - ``data/data.py`` class-level parsing di ``GlobalText`` (baris 12-86)

Perbaikan dibanding kode asli:
  - Decode hanya dilakukan **sekali** (bukan puluhan kali seperti di data.py).
  - Section dicari secara dinamis lewat loop, bukan copy-paste per instrumen.
  - Encoding dideteksi dengan BOM + UTF-8 strict + fallback legacy, dan
    encoding asli disimpan untuk dipakai lagi saat save.
  - Posisi body ``[Events]`` disimpan supaya writer bisa mempertahankan
    seluruh isi file di luar body tersebut.
  - Tidak ada state global; hasilnya dikembalikan sebagai ChartDocument.
"""
from __future__ import annotations

import re
import textwrap
from pathlib import Path
from typing import Union

from core.chart.document import (
    DIFFICULTIES,
    INSTRUMENTS,
    ChartDocument,
    detect_newline,
)
from core.chart.encoding import decode_bytes


# ─────────────────────────────────────────────────────────────────────────────
#  Section scanner
# ─────────────────────────────────────────────────────────────────────────────

# Header section harus berada di awal baris. Ini mencegah teks lirik seperti
# ``0 = E "lyric [Song]"`` ikut terdeteksi sebagai section.
_SECTION_HEADER_RE = re.compile(r"(?m)^[ \t]*\[([^\]\r\n]+)\][ \t]*\r?$")


def _find_matching_brace(text: str, open_index: int) -> int:
    """Cari ``}`` pasangan dari ``{`` di *open_index*.

    Brace di dalam string (mis. lirik ``E "lyric a}b"``) diabaikan.
    Mengembalikan -1 jika tidak ditemukan.
    """
    depth = 0
    in_quote = False
    escaped = False

    for index in range(open_index, len(text)):
        char = text[index]

        if in_quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_quote = False
            continue

        if char == '"':
            in_quote = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index

    return -1


def _find_section_span(text: str, section_name: str) -> tuple[int, int, int] | None:
    """Cari satu section dan kembalikan ``(header_start, brace_open, brace_close)``.

    ``header_start`` adalah indeks awal ``[SectionName]``; ``brace_open`` dan
    ``brace_close`` adalah indeks ``{`` dan ``}`` pembungkus section.
    """
    for match in _SECTION_HEADER_RE.finditer(text):
        if match.group(1).strip() != section_name:
            continue

        brace_open = text.find("{", match.end())
        if brace_open == -1:
            continue
        # Pastikan tidak ada section lain di antara header dan brace.
        if text[match.end() : brace_open].strip():
            continue

        brace_close = _find_matching_brace(text, brace_open)
        if brace_close == -1:
            continue

        return match.start(), brace_open, brace_close

    return None


def _extract_section(text: str, section_name: str) -> str:
    """Ekstrak satu section ``[SectionName]`` beserta isi di dalam ``{ … }``-nya.

    Mengembalikan string dari ``[SectionName]`` hingga ``}`` penutup.
    Jika section tidak ditemukan, mengembalikan string kosong.
    """
    span = _find_section_span(text, section_name)
    if span is None:
        return ""
    start, _brace_open, brace_close = span
    return text[start : brace_close + 1]


def _normalise_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _prepare_events_body(body_raw: str) -> str:
    """Ubah body mentah menjadi teks editor yang bersih.

    - Semua line ending diseragamkan ke ``\\n`` (QPlainTextEdit memakai ``\\n``).
    - Baris kosong di awal/akhir dibuang.
    - Indentasi umum (spasi/tab) dihapus, bukan hanya dua spasi seperti kode lama.
    """
    lines = _normalise_newlines(body_raw).split("\n")

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        return ""

    return textwrap.dedent("\n".join(lines))


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

def parse_chart_file(
    path: Union[str, Path],
    *,
    encoding: str | None = None,
) -> ChartDocument:
    """Baca dan parse file .chart dari *path*.

    Args:
        path:     Lokasi file .chart.
        encoding: Paksa encoding tertentu (mis. ``"shift_jis"``). Jika ``None``,
                  encoding dideteksi otomatis.

    Returns:
        ChartDocument yang berisi semua section terparsing.

    Raises:
        FileNotFoundError: Jika file tidak ditemukan.
        ValueError: Jika encoding paksa tidak valid / isi tidak bisa di-decode.
    """
    path = Path(path)
    raw_bytes = path.read_bytes()
    return parse_chart_bytes(raw_bytes, file_path=str(path), encoding=encoding)


def parse_chart_bytes(
    raw: bytes,
    *,
    file_path: str | None = None,
    encoding: str | None = None,
) -> ChartDocument:
    """Parse bytes mentah dari file .chart.

    Ini adalah fungsi parsing inti yang bisa dipanggil tanpa file fisik
    (berguna untuk testing).
    """
    decoded = decode_bytes(raw, encoding=encoding)
    text = decoded.text
    newline = detect_newline(text)

    # ── Section utama ────────────────────────────────────────────────────
    song = _extract_section(text, "Song")
    sync_track = _extract_section(text, "SyncTrack")
    events_span = _find_section_span(text, "Events")

    # ── Pisahkan events menjadi header (dengan placeholder) dan body ────
    events_body = ""
    events_header = ""
    events_body_start = -1
    events_body_end = -1

    if events_span is not None:
        header_start, brace_open, brace_close = events_span
        events_body = _prepare_events_body(text[brace_open + 1 : brace_close])
        events_header = (
            text[header_start : brace_open + 1]
            + "\n"
            + ChartDocument.PLACEHOLDER
            + "\n}"
            + newline
        )
        events_body_start = brace_open + 1
        events_body_end = brace_close

    # ── Section instrumen / difficulty ───────────────────────────────────
    note_sections_parts: list[str] = []
    for inst in INSTRUMENTS:
        for diff in DIFFICULTIES:
            section_name = diff + inst          # e.g. "ExpertSingle"
            section = _extract_section(text, section_name)
            if section:
                note_sections_parts.append(section)

    note_sections = newline.join(note_sections_parts)
    if note_sections:
        note_sections += newline

    return ChartDocument(
        song=song + newline if song else "",
        sync_track=sync_track + newline if sync_track else "",
        events_header=events_header + newline if events_header else "",
        events_body=events_body,
        note_sections=note_sections,
        file_path=file_path,
        encoding=decoded.encoding,
        bom=decoded.bom,
        raw_text=text,
        raw_bytes=raw,
        events_body_start=events_body_start,
        events_body_end=events_body_end,
        newline=newline,
        encoding_confidence=decoded.confidence,
        encoding_warning=decoded.warning,
    )
