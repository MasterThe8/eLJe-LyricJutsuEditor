"""Daftar simbol lirik Clone Hero: pembaca ``assets/symbols/CH_Lyric_Symbols.txt`` dan fungsi pencariannya.

Murni Python, tanpa dependensi GUI. Lokasi file ditentukan pemanggil (lihat ``services.text_assets``), sehingga
modul ini tidak menyimpan salinan data simbol sendiri: file ``.txt`` adalah satu-satunya sumber.

Format file::

    <kata pengantar bebas — semua baris sebelum header pertama diabaikan>

    Letters                  <- header kategori: baris hanya huruf ASCII (boleh spasi), didahului baris kosong
    α β γ δ ...              <- baris simbol: dipisah spasi, boleh beberapa baris
    Α Β Γ Δ ...

    Math
    ⁺ ⁻ ⁼ ...

Catatan: baris pengantar yang HANYA berisi huruf ASCII (tanpa angka/tanda baca) akan terbaca sebagai header kategori.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

# Header kategori: hanya huruf ASCII (dan spasi antar kata), di baris yang didahului baris kosong / awal file.
_HEADER = re.compile(r"[A-Za-z]+(?: [A-Za-z]+)*")


def parse_symbols(text: str) -> dict[str, str]:
    """Teks file simbol → ``{kategori: karakter}`` (urutan file; spasi dibuang, duplikat dalam kategori dibiarkan).

    Baris sebelum header pertama (kata pengantar) diabaikan, begitu pula kategori tanpa simbol.
    ``ValueError`` bila tidak ada satu pun kategori berisi simbol.
    """
    categories: dict[str, list[str]] = {}
    current: str | None = None
    previous_blank = True
    for line in text.splitlines():
        stripped = line.strip()
        if previous_blank and _HEADER.fullmatch(stripped):
            current = stripped
            categories.setdefault(current, [])
        elif stripped and current is not None:
            categories[current].append("".join(c for c in stripped if not c.isspace()))
        previous_blank = not stripped
    result = {name: "".join(parts) for name, parts in categories.items() if parts}
    if not any(result.values()):
        raise ValueError("no symbol categories found")
    return result


def load_symbols(path: str | Path) -> dict[str, str]:
    """Baca dan urai file simbol. ``OSError`` / ``UnicodeDecodeError`` / ``ValueError`` bila file tak bisa dipakai."""
    return parse_symbols(Path(path).read_text(encoding="utf-8-sig"))


def all_symbols(symbols: dict[str, str], category: str = "All") -> list[str]:
    """Daftar karakter unik (urutan file), tanpa spasi. ``category`` = nama kategori atau ``"All"``."""
    chars = "".join(symbols.values()) if category == "All" else symbols.get(category, "")
    return list(dict.fromkeys(c for c in chars if not c.isspace()))


def symbol_name(ch: str) -> str:
    try:
        return unicodedata.name(ch).title()
    except ValueError:
        return "Unnamed symbol"


def matches(ch: str, query: str) -> bool:
    """Cocokkan karakter, kode (mis. 2605 / U+2605), atau nama Unicode (mis. star)."""
    q = query.strip()
    if not q:
        return True
    if q in ch:
        return True
    code = q.upper().replace("U+", "")
    if code and all(c in "0123456789ABCDEF" for c in code) and f"{ord(ch):04X}".startswith(code):
        return True
    try:
        return q.upper() in unicodedata.name(ch)
    except ValueError:
        return False
