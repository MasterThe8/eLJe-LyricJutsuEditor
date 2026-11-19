"""Setting aplikasi: nilai aktif (di memori) + penyimpanan persisten ala Appearance.

Alurnya sama untuk semua setting:

1. Startup: ``load_settings()`` (dipanggil ``app.py`` sebelum jendela dibuat) membaca nilai tersimpan, MEMVALIDASINYA,
   lalu mengisi dict global di bawah. Nilai hilang / rusak / di luar batas diganti nilai bawaan per-kunci,
   jadi satu nilai buruk tidak menggagalkan yang lain.
2. Runtime: dialog / aksi memanggil ``update_*``: nilai divalidasi, dict global diperbarui, lalu langsung disimpan
   (tanpa tombol "Save"), persis seperti Appearance.

Dict global (``HIGHLIGHT``, ``SHORTCUTS``, ``LYRIC_SETTINGS``, ``EDITOR_FONTS``, ``VIEW``, ``PATHS``) selalu diubah
DI TEMPAT (``.update``), tidak pernah diganti objeknya: modul yang mengimpornya (atau memakainya sebagai default
argument, mis. ``LyricHighlighter``) otomatis melihat nilai terbaru.

Kunci penyimpanan (``QSettings(MasterThe8, eLJe)``; di Windows: ``HKCU\\Software\\MasterThe8\\eLJe``)::

    appearance/theme                                  id tema
    highlight/{position,value,richtag,eventname}      warna #RRGGBB
    lyric/{closing_lyric,hidden_lyric}                teks
    shortcuts/<nama aksi>                             urutan tombol (PortableText); kosong = tanpa shortcut
    editor/{plain,rich}/{family,size,bold,italic}     font editor; family kosong = font bawaan editor
    view/{display,treeview,temptext}                  panel yang tampil
    paths/chart_dir                                   folder lagu di panel Directory
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from services.defaults import (
    DEFAULT_FONT_PLAIN,
    DEFAULT_FONT_RICH,
    DEFAULT_HIGHLIGHT,
    DEFAULT_LYRIC,
    DEFAULT_SHORTCUTS,
    DEFAULT_VIEW,
    DEFAULTS,
)
from services.settings_store import SETTINGS_APP, SETTINGS_ORG, SettingsStore, default_store  # noqa: F401

# ─────────────────────────────────────────────────────────────────────────────
#  Nilai aktif
# ─────────────────────────────────────────────────────────────────────────────
HIGHLIGHT = dict(DEFAULT_HIGHLIGHT)         # warna sintaks editor; dialog Highlight
SHORTCUTS = dict(DEFAULT_SHORTCUTS)         # dialog Hotkey
LYRIC_SETTINGS = dict(DEFAULT_LYRIC)        # dialog LyricJutsu
EDITOR_FONTS = {"plain": dict(DEFAULT_FONT_PLAIN), "rich": dict(DEFAULT_FONT_RICH)}   # dialog Font + Zoom
VIEW = dict(DEFAULT_VIEW)                   # toggle panel (menu View / toolbar)
PATHS = {"chart_dir": DEFAULTS["chart_dir"]}

# ─────────────────────────────────────────────────────────────────────────────
#  Skema: kunci dan batas nilai
# ─────────────────────────────────────────────────────────────────────────────
KEY_THEME = "appearance/theme"
DEFAULT_THEME_ID = "default"

LYRIC_MAX_LEN = 12                          # sama dengan batas kolom di dialog LyricJutsu
SHORTCUT_MAX_LEN = 64
FONT_FAMILY_MAX_LEN = 128
FONT_SIZE_MIN, FONT_SIZE_MAX = 6, 72        # rentang spinbox dialog Font
CHART_DIR_MAX_LEN = 1024

_HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{6}")
_FONT_DEFAULTS = {"plain": DEFAULT_FONT_PLAIN, "rich": DEFAULT_FONT_RICH}


def _store(store: SettingsStore | None) -> SettingsStore:
    return store or default_store()


# ─────────────────────────────────────────────────────────────────────────────
#  Validasi (dipakai oleh pemuatan DAN pembaruan, jadi keduanya menerapkan aturan yang sama)
# ─────────────────────────────────────────────────────────────────────────────
def _clean_highlight(raw: Mapping[str, Any]) -> dict[str, str]:
    out = {}
    for key, default in DEFAULT_HIGHLIGHT.items():
        value = raw.get(key)
        text = value.strip() if isinstance(value, str) else ""
        out[key] = text.upper() if _HEX_COLOR.fullmatch(text) else default
    return out


def _clean_lyric(raw: Mapping[str, Any]) -> dict[str, str]:
    out = {}
    for key, default in DEFAULT_LYRIC.items():
        value = raw.get(key)
        out[key] = value if isinstance(value, str) and len(value) <= LYRIC_MAX_LEN else default
    return out


def _clean_shortcuts(raw: Mapping[str, Any]) -> dict[str, str]:
    """Kunci tak dikenal dibuang; kunci yang belum ada (mis. shortcut baru di versi berikutnya) memakai bawaan."""
    out = {}
    for key, default in DEFAULT_SHORTCUTS.items():
        value = raw.get(key)
        out[key] = value.strip() if isinstance(value, str) and len(value) <= SHORTCUT_MAX_LEN else default
    return out


def _clean_font(raw: Mapping[str, Any], default: Mapping[str, Any]) -> dict[str, Any]:
    family = raw.get("family")
    family = family.strip() if isinstance(family, str) and len(family) <= FONT_FAMILY_MAX_LEN else ""
    size = raw.get("size")
    size = size if isinstance(size, int) and not isinstance(size, bool) else default["size"]
    bold, italic = raw.get("bold"), raw.get("italic")
    return {
        "family": family,
        "size": max(FONT_SIZE_MIN, min(FONT_SIZE_MAX, size)),
        "bold": bold if isinstance(bold, bool) else default["bold"],
        "italic": italic if isinstance(italic, bool) else default["italic"],
    }


def _save(prefix: str, data: Mapping[str, Any], store: SettingsStore | None) -> bool:
    return _store(store).set_many({f"{prefix}/{key}": value for key, value in data.items()})


# ─────────────────────────────────────────────────────────────────────────────
#  Pemuatan (startup)
# ─────────────────────────────────────────────────────────────────────────────
def load_settings(store: SettingsStore | None = None) -> None:
    """Isi semua dict global dari penyimpanan. Aman dipanggil dengan penyimpanan kosong / rusak (→ nilai bawaan).

    Harus dipanggil SEBELUM MainWindow dibuat: shortcut, warna highlight, font, dan panel dibaca saat jendela dibangun.
    """
    store = _store(store)

    HIGHLIGHT.update(_clean_highlight({k: store.get_str(f"highlight/{k}", "") for k in DEFAULT_HIGHLIGHT}))
    LYRIC_SETTINGS.update(_clean_lyric({
        k: store.get_str(f"lyric/{k}", default, max_len=LYRIC_MAX_LEN) for k, default in DEFAULT_LYRIC.items()}))
    SHORTCUTS.update(_clean_shortcuts({
        k: store.get_str(f"shortcuts/{k}", default, max_len=SHORTCUT_MAX_LEN)
        for k, default in DEFAULT_SHORTCUTS.items()}))

    for kind, default in _FONT_DEFAULTS.items():
        prefix = f"editor/{kind}"
        EDITOR_FONTS[kind].update(_clean_font({
            "family": store.get_str(f"{prefix}/family", "", max_len=FONT_FAMILY_MAX_LEN),
            "size": store.get_int(f"{prefix}/size", default["size"], FONT_SIZE_MIN, FONT_SIZE_MAX),
            "bold": store.get_bool(f"{prefix}/bold", default["bold"]),
            "italic": store.get_bool(f"{prefix}/italic", default["italic"]),
        }, default))

    for key, default in DEFAULT_VIEW.items():
        VIEW[key] = store.get_bool(f"view/{key}", default)

    chart_dir = store.get_str("paths/chart_dir", DEFAULTS["chart_dir"], max_len=CHART_DIR_MAX_LEN).strip()
    PATHS["chart_dir"] = chart_dir or DEFAULTS["chart_dir"]


# ─────────────────────────────────────────────────────────────────────────────
#  Pembaruan (runtime): validasi → perbarui nilai aktif → simpan
#  Mengembalikan nilai AKTIF setelah validasi (salinan), bukan masukan mentah.
# ─────────────────────────────────────────────────────────────────────────────
def update_highlight(colors: Mapping[str, Any], store: SettingsStore | None = None) -> dict[str, str]:
    HIGHLIGHT.update(_clean_highlight({**HIGHLIGHT, **colors}))
    _save("highlight", HIGHLIGHT, store)
    return dict(HIGHLIGHT)


def update_lyric_settings(values: Mapping[str, Any], store: SettingsStore | None = None) -> dict[str, str]:
    LYRIC_SETTINGS.update(_clean_lyric({**LYRIC_SETTINGS, **values}))
    _save("lyric", LYRIC_SETTINGS, store)
    return dict(LYRIC_SETTINGS)


def update_shortcuts(data: Mapping[str, Any], store: SettingsStore | None = None) -> dict[str, str]:
    SHORTCUTS.update(_clean_shortcuts({**SHORTCUTS, **data}))
    _save("shortcuts", SHORTCUTS, store)
    return dict(SHORTCUTS)


def update_editor_fonts(changes: Mapping[str, Mapping[str, Any]],
                        store: SettingsStore | None = None) -> dict[str, dict[str, Any]]:
    """``changes``: ``{"plain": {...}, "rich": {...}}``; hanya kolom yang diberikan yang berubah (mis. ukuran saat Zoom)."""
    items: dict[str, Any] = {}
    for kind, fields in changes.items():
        if kind not in EDITOR_FONTS:
            continue
        EDITOR_FONTS[kind].update(_clean_font({**EDITOR_FONTS[kind], **fields}, _FONT_DEFAULTS[kind]))
        items.update({f"editor/{kind}/{key}": value for key, value in EDITOR_FONTS[kind].items()})
    if items:
        _store(store).set_many(items)
    return {kind: dict(spec) for kind, spec in EDITOR_FONTS.items()}


def update_view(key: str, visible: bool, store: SettingsStore | None = None) -> None:
    if key in VIEW:
        VIEW[key] = bool(visible)
        _store(store).set(f"view/{key}", VIEW[key])


def update_chart_dir(path: str, store: SettingsStore | None = None) -> None:
    path = str(path).strip()
    if path and len(path) <= CHART_DIR_MAX_LEN:
        PATHS["chart_dir"] = path
        _store(store).set("paths/chart_dir", path)


# ─────────────────────────────────────────────────────────────────────────────
#  Tema (Appearance). Hanya ID yang disimpan, bukan warna; validasi terhadap registry oleh ThemeManager.
# ─────────────────────────────────────────────────────────────────────────────
def load_theme_id(store: SettingsStore | None = None) -> str:
    """ID tema tersimpan; 'default' bila belum ada / rusak."""
    return _store(store).get_str(KEY_THEME, DEFAULT_THEME_ID).strip() or DEFAULT_THEME_ID


def save_theme_id(theme_id: str, store: SettingsStore | None = None) -> None:
    _store(store).set(KEY_THEME, theme_id)
