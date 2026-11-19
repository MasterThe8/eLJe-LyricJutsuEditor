"""Registry tema. Menambah tema baru: buat modul di sini (dict ``THEME``) lalu daftarkan di ``_MODULES``.

Semua tema wajib punya himpunan token yang sama dengan ``TOKEN_KEYS`` — divalidasi saat import,
jadi tema yang tidak lengkap langsung ketahuan.
"""
from __future__ import annotations

from ui.theme.tokens import TOKEN_KEYS

from . import amoled, default, dracula, nord, tokyo_night

DEFAULT_THEME_ID = "default"

_MODULES = (default, dracula, nord, tokyo_night, amoled)       # urutan = urutan di daftar pilihan


def validate_theme(theme: dict) -> list[str]:
    """Kembalikan daftar masalah (kosong = valid)."""
    problems = []
    colors = theme.get("colors", {})
    for key in ("id", "name", "description"):
        if not theme.get(key):
            problems.append(f"missing '{key}'")
    for k in TOKEN_KEYS:
        if k not in colors:
            problems.append(f"missing token {k}")
    for k in colors:
        if k not in TOKEN_KEYS:
            problems.append(f"unknown token {k}")
    return problems


def _build_registry() -> dict[str, dict]:
    registry: dict[str, dict] = {}
    for mod in _MODULES:
        theme = mod.THEME
        problems = validate_theme(theme)
        if problems:
            raise ValueError(f"Invalid theme '{theme.get('id', mod.__name__)}': {'; '.join(problems)}")
        if theme["id"] in registry:
            raise ValueError(f"Duplicate theme id '{theme['id']}'")
        registry[theme["id"]] = theme
    if DEFAULT_THEME_ID not in registry:
        raise ValueError("Default theme is not registered")
    return registry


THEMES: dict[str, dict] = _build_registry()

__all__ = ["DEFAULT_THEME_ID", "THEMES", "validate_theme"]
