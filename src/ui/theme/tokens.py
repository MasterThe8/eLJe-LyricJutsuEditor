"""Token desain (warna permukaan, teks, aksen) dengan token aktif yang dapat diganti saat runtime.

Tiga lapis permukaan: CHROME (bingkai) < PANEL (dock) < EDITOR (area kerja).
Nilai awal ``Theme`` = tema "Default Dark" (EDITOR = background_color asli #282a36,
aksen cyan = warna judul landing asli).

Pemakaian lama ``Theme.ACCENT`` tetap berfungsi: ``set_active_theme()`` menulis ulang atribut
kelas ``Theme``, jadi kode yang membaca ``Theme.X`` saat dipakai (bukan saat import) selalu
melihat nilai terbaru. Jangan menyalin ``Theme.X`` ke default-argument / konstanta modul.
"""
from __future__ import annotations

import re
from typing import Mapping


class Theme:
    """Token tema aktif. Atribut diisi ulang oleh ``set_active_theme``."""
    # permukaan
    CHROME = "#1c1d2b"
    PANEL = "#222335"
    EDITOR = "#282a36"
    RAISED = "#2f3148"
    BORDER = "#34364d"
    BORDER_HI = "#4a4e72"
    # teks
    TEXT = "#eceef7"
    DIM = "#a3a8c2"
    FAINT = "#7d82a3"
    EDITOR_TEXT = "#f2f3f8"
    # aksen & seleksi
    ACCENT = "#1beef5"
    ACCENT_SOFT = "rgba(27, 238, 245, 36)"
    SELECTION = "#3f4363"
    SELECTION_TEXT = "#ffffff"
    DANGER = "#ff6b81"
    # editor
    GUTTER = "#242632"
    LINE_HIGHLIGHT = "rgba(255, 255, 255, 14)"
    ERROR_LINE = "rgba(230, 40, 50, 100)"          # latar baris script berstruktur salah (PlainText editor)
    # scrollbar
    SCROLLBAR = "#3d4060"
    SCROLLBAR_HOVER = "#565a86"
    # tombol primer
    PRIMARY_TEXT = "#05252a"
    PRIMARY_HOVER = "#5af4f9"
    # callout (peringatan)
    CALLOUT_BG = "rgba(255, 169, 77, 26)"
    CALLOUT_BORDER = "rgba(255, 169, 77, 80)"
    CALLOUT_TEXT = "#ffc78a"
    # ilustrasi layar lirik mini
    MOCK_SCREEN = "#161725"


#: Daftar token wajib (urutan = urutan deklarasi di ``Theme``).
TOKEN_KEYS: tuple[str, ...] = tuple(k for k, v in vars(Theme).items() if k.isupper() and isinstance(v, str))

_active: dict[str, str] = {k: getattr(Theme, k) for k in TOKEN_KEYS}


def get_active_theme() -> dict[str, str]:
    """Salinan token tema yang sedang aktif (mengubah salinan tidak berpengaruh)."""
    return dict(_active)


def set_active_theme(colors: Mapping[str, str]) -> None:
    """Ganti token aktif. ``colors`` harus memuat semua token wajib; bila tidak, ValueError
    dan token aktif tidak berubah (all-or-nothing)."""
    missing = [k for k in TOKEN_KEYS if k not in colors]
    if missing:
        raise ValueError(f"Theme is missing tokens: {', '.join(missing)}")
    new = {k: str(colors[k]) for k in TOKEN_KEYS}
    _active.update(new)
    for k, v in new.items():
        setattr(Theme, k, v)


_RGBA = re.compile(r"^\s*rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d+)\s*)?\)\s*$", re.I)


def to_qcolor(value: str):
    """Ubah nilai token menjadi QColor. Mendukung '#rrggbb' dan 'rgba(r, g, b, a)' (a: 0-255,
    sama seperti QSS) — QColor sendiri tidak bisa mem-parse format rgba() itu."""
    from PySide6.QtGui import QColor   # impor lambat: modul ini tetap bisa dipakai tanpa Qt

    m = _RGBA.match(value)
    if m:
        r, g, b, a = m.groups()
        return QColor(int(r), int(g), int(b), 255 if a is None else int(a))
    return QColor(value)
