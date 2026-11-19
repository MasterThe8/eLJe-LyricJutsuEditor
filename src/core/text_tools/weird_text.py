"""Weird Text Generator: ubah huruf A–Z menjadi alfabet dekoratif dari ``assets/weird_text/wt1 … wt26``.

Murni Python, tanpa dependensi GUI. Lokasi folder ditentukan pemanggil (lihat ``services.text_assets``).

Format satu file gaya (``wtN``): satu baris berisi tampilan huruf A sampai Z secara berurutan, mis.
``ＡＢＣ…`` (satu karakter per huruf), ``A̶B̶C̶…`` (huruf + combining mark), atau ``【A】【B】…`` (dibungkus).
Panjang tiap huruf tidak ditulis di file: karakter dikelompokkan per "karakter + combining mark" lalu dibagi
rata menjadi 26 bagian, sehingga ketiga bentuk itu terbaca tanpa konfigurasi tambahan.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ALPHABET_SIZE = 26

_STYLE_FILE = re.compile(r"wt(\d+)", re.IGNORECASE)
# Tag lirik (``<color=#FF0000>``, ``</b>``, ``<br>`` …) tidak boleh ikut diubah, sama seperti ``convert_symbols``.
_TAG_SPLIT = re.compile(r"(<[^>]*>)")


@dataclass(frozen=True)
class WeirdStyle:
    """Satu alfabet dekoratif. ``glyphs[0]`` adalah tampilan A/a, ``glyphs[25]`` tampilan Z/z."""
    name: str                       # nama file, mis. "wt7"
    glyphs: tuple[str, ...]


def _clusters(text: str) -> list[str]:
    """Pecah teks menjadi karakter dasar + combining mark yang menempel padanya."""
    result: list[str] = []
    for ch in text:
        if result and unicodedata.category(ch).startswith("M"):
            result[-1] += ch
        else:
            result.append(ch)
    return result


def parse_style(name: str, content: str) -> WeirdStyle:
    """Isi file → ``WeirdStyle``. ``ValueError`` bila jumlah karakternya tidak habis dibagi 26."""
    clusters = _clusters(content.strip())
    count = len(clusters)
    if count == 0 or count % ALPHABET_SIZE:
        raise ValueError(f"expected 26 letters (or a multiple of 26 characters), found {count}")
    size = count // ALPHABET_SIZE
    glyphs = tuple("".join(clusters[i * size:(i + 1) * size]) for i in range(ALPHABET_SIZE))
    return WeirdStyle(name, glyphs)


def load_weird_styles(directory: str | Path) -> tuple[list[WeirdStyle], list[str]]:
    """Baca semua ``wtN`` di ``directory``, urut menurut N (wt2 sebelum wt10).

    Mengembalikan ``(gaya, masalah)``. File yang tidak terbaca / formatnya salah dilewati dan dilaporkan di
    ``masalah`` (teks siap tampil) — satu file rusak tidak menggagalkan gaya lainnya.
    """
    directory = Path(directory)
    if not directory.is_dir():
        return [], [f"folder not found: {directory}"]
    files = sorted(
        (int(match.group(1)), path)
        for path in directory.iterdir()
        if path.is_file() and (match := _STYLE_FILE.fullmatch(path.name))
    )
    styles: list[WeirdStyle] = []
    problems: list[str] = []
    for _number, path in files:
        try:
            styles.append(parse_style(path.name, path.read_text(encoding="utf-8-sig")))
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            problems.append(f"{path.name}: {exc}")
    return styles, problems


def _letter_index(ch: str) -> int:
    code = ord(ch)
    if 65 <= code <= 90:            # A–Z
        return code - 65
    if 97 <= code <= 122:           # a–z: sama dengan huruf besarnya (file hanya memuat satu set)
        return code - 97
    return -1


def convert(text: str, style: WeirdStyle) -> str:
    """Ganti tiap huruf A–Z/a–z dengan tampilannya di ``style``. Karakter lain dan isi tag ``<…>`` dibiarkan."""
    parts = _TAG_SPLIT.split(text)
    for index in range(0, len(parts), 2):               # indeks genap = teks biasa, ganjil = tag
        parts[index] = "".join(
            style.glyphs[i] if (i := _letter_index(ch)) >= 0 else ch for ch in parts[index]
        )
    return "".join(parts)


def convert_all(text: str, styles: list[WeirdStyle]) -> list[str]:
    """Hasil ``convert`` untuk setiap gaya, searah dengan ``styles``."""
    return [convert(text, style) for style in styles]
