"""Lokasi dan pembaca data teks di folder ``assets/``: daftar simbol (Get Symbol) dan alfabet Weird Text.

Parsernya ada di ``core.text_tools`` (murni Python); modul ini hanya tahu DI MANA file-nya dan menerjemahkan
kegagalan baca menjadi ``AssetError`` dengan pesan yang bisa langsung ditampilkan ke pengguna.

Tidak ada cache di sini: file dibaca ulang tiap pemanggilan (kecil dan jarang dipanggil). Gaya Weird Text dibaca
tiap klik Generate, jadi hasil edit ``wtN`` langsung terpakai. Daftar simbol dibaca saat panel Symbol Picker dibuat
(startup) dan saat jendela Get Symbol pertama kali dibuka; jendelanya dipakai ulang, jadi edit ``.txt`` baru
terlihat setelah aplikasi dibuka ulang.
"""
from __future__ import annotations

from core.text_tools.symbols import load_symbols
from core.text_tools.weird_text import WeirdStyle, load_weird_styles
from services.paths import ASSETS_DIR


SYMBOLS_FILE = ASSETS_DIR / "symbols" / "CH_Lyric_Symbols.txt"
WEIRD_TEXT_DIR = ASSETS_DIR / "weird_text"


class AssetError(Exception):
    """Data assets tidak bisa dipakai; ``str(error)`` adalah pesan untuk pengguna."""


def read_symbols() -> dict[str, str]:
    """``{kategori: karakter}`` dari ``CH_Lyric_Symbols.txt``. ``AssetError`` bila file hilang / rusak."""
    try:
        return load_symbols(SYMBOLS_FILE)
    except FileNotFoundError:
        raise AssetError(f"Symbol file not found: {SYMBOLS_FILE}") from None
    except (OSError, UnicodeDecodeError) as exc:
        raise AssetError(f"Could not read {SYMBOLS_FILE.name}: {exc}") from exc
    except ValueError:
        raise AssetError(f"{SYMBOLS_FILE.name} has no symbol categories.") from None


def read_weird_styles() -> tuple[list[WeirdStyle], list[str]]:
    """``(gaya, masalah)`` dari ``weird_text/wt1…wt26``; lihat ``core.text_tools.weird_text.load_weird_styles``."""
    return load_weird_styles(WEIRD_TEXT_DIR)
