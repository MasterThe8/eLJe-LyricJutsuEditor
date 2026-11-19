"""Lokasi folder ``assets/`` — satu sumber untuk data teks (simbol, Weird Text) dan ikon/logo aplikasi.

Murni Python, tanpa dependensi GUI.
"""
from __future__ import annotations

import sys
from pathlib import Path


def _base_dir() -> Path:
    """Akar tempat folder ``assets/`` berada: folder paket ``src`` saat dijalankan biasa, atau folder ekstraksi
    PyInstaller (``sys._MEIPASS``) pada build ter-bundel (``assets`` harus ikut dibundel sebagai data)."""
    frozen = getattr(sys, "_MEIPASS", None)
    return Path(frozen) if frozen else Path(__file__).resolve().parent.parent


ASSETS_DIR = _base_dir() / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
