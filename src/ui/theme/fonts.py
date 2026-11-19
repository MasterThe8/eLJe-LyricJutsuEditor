"""Font aplikasi: monospace untuk editor/pratinjau, dan rantai font untuk simbol/emoji."""
from __future__ import annotations

from collections.abc import Mapping
from functools import lru_cache
from typing import Any

from PySide6.QtGui import QFont, QFontDatabase


def mono_font(size: int) -> QFont:
    f = QFont()
    f.setFamilies(["JetBrains Mono", "Cascadia Code", "Cascadia Mono", "SF Mono",
                   "Menlo", "Consolas", "DejaVu Sans Mono", "monospace"])
    f.setStyleHint(QFont.StyleHint.Monospace)
    f.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    f.setPointSize(size)
    return f

def editor_font(spec: Mapping[str, Any], base: QFont) -> QFont:
    """Font editor dari setting tersimpan (``services.settings.EDITOR_FONTS``).

    ``family`` kosong, atau font itu sudah tidak terpasang di komputer ini → pakai ``base`` (font bawaan editor),
    bukan font cadangan acak pilihan Qt. Ukuran dan gaya tetap dari ``spec``.
    """
    family = str(spec.get("family") or "")
    font = QFont(family) if family and family.casefold() in _installed_families() else QFont(base)
    font.setPointSize(int(spec["size"]))
    font.setBold(bool(spec["bold"]))
    font.setItalic(bool(spec["italic"]))
    return font


# ─────────────────────────────────────────────────────────────────────────────
#  Font simbol dan emoji
# ─────────────────────────────────────────────────────────────────────────────
# Qt memakai daftar ``setFamilies`` sebagai rantai fallback PER GLYPH: tiap karakter digambar oleh font pertama di
# daftar yang memilikinya. Karena itu URUTAN menentukan tampilan, bukan hanya cakupan.
#
# Font SIMBOL (monokrom) harus di depan. Bila font emoji di depan, simbol teks seperti © ® ♠ ♣ ♥ ♦ ☺ ☹ ⚠ ikut
# digambar sebagai gambar emoji: warnanya tidak mengikuti tema, dan yang berwarna hitam (♠ ♣) hampir tak terlihat di
# tema gelap. Font emoji hanya dipakai untuk karakter yang memang emoji (lihat ``is_emoji``).
#
# Daftar ini berurutan menurut cakupan blok Unicode pada ``assets/symbols/CH_Lyric_Symbols.txt``: simbol / panah /
# bentuk / box drawing (Segoe UI Symbol), matematika & huruf modifier (Cambria Math, Segoe UI), CJK / full-half-width
# / bentuk vertikal (YaHei, Yu Gothic, MS Gothic), Hangul (Malgun Gothic). Nama yang tidak terpasang dilewati.
# Urutan: Windows, macOS, lalu Linux; satu daftar cukup karena hanya font yang terpasang yang dipakai.
_SYMBOL_FAMILIES = (
    # Windows
    "Segoe UI Symbol", "Segoe UI", "Cambria Math", "Microsoft YaHei UI", "Yu Gothic UI", "Meiryo UI",
    "Malgun Gothic", "MS Gothic", "Microsoft JhengHei UI", "SimSun", "Leelawadee UI", "Arial Unicode MS",
    "Segoe UI Historic",
    # macOS
    "Apple Symbols", "Menlo", "Hiragino Sans", "Apple SD Gothic Neo", "PingFang SC", "STIXGeneral",
    # Linux
    "DejaVu Sans", "Noto Sans Symbols", "Noto Sans Symbols 2", "Noto Sans Math", "Noto Sans CJK JP",
    "Noto Sans CJK KR", "Noto Sans CJK SC", "Droid Sans Fallback", "Unifont", "FreeSans",
)
_EMOJI_FAMILIES = ("Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", "Twemoji Mozilla", "Noto Emoji")
_PLAIN_FALLBACK = ["Segoe UI", "Arial"]               # bila tak satu pun font di atas terpasang
_EMOJI_FIRST_CODEPOINT = 0x1F000                      # blok piktograf/emoji (🤣 😂 🆗 …) ada di luar BMP


@lru_cache(maxsize=1)
def _installed_families() -> frozenset[str]:
    return frozenset(name.casefold() for name in QFontDatabase.families())


def _installed(candidates: tuple[str, ...]) -> list[str]:
    installed = _installed_families()
    return [name for name in candidates if name.casefold() in installed]


def _make_font(families: list[str], size: int) -> QFont:
    font = QFont()
    font.setFamilies(families or _PLAIN_FALLBACK)
    font.setPointSize(size)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return font


def symbol_font(size: int) -> QFont:
    """Font simbol monokrom (mengikuti warna teks tema). Dipakai untuk semua karakter selain emoji."""
    return _make_font(_installed(_SYMBOL_FAMILIES) + _installed(_EMOJI_FAMILIES), size)


def emoji_font(size: int) -> QFont:
    """Font emoji berwarna lebih dulu, lalu rantai simbol sebagai cadangan."""
    return _make_font(_installed(_EMOJI_FAMILIES) + _installed(_SYMBOL_FAMILIES), size)


def is_emoji(ch: str) -> bool:
    """Karakter piktograf/emoji yang sebaiknya digambar berwarna (semua berada di luar BMP, ≥ U+1F000)."""
    return bool(ch) and ord(ch[0]) >= _EMOJI_FIRST_CODEPOINT


@lru_cache(maxsize=None)
def _font_for(emoji: bool, size: int) -> QFont:
    return emoji_font(size) if emoji else symbol_font(size)


def font_for_symbol(ch: str, size: int) -> QFont:
    """Font terbaik untuk ``ch``: emoji → font emoji berwarna; selain itu → font simbol monokrom. Salinan baru."""
    return QFont(_font_for(is_emoji(ch), size))
