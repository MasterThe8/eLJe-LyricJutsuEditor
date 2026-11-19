"""Ikon vektor SVG inline dan renderer-nya."""
from __future__ import annotations

import weakref
from typing import Callable

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from ui.theme.tokens import get_active_theme

# ─────────────────────────────────────────────────────────────────────────────
#  Ikon vektor (SVG inline, gaya garis 24x24) — tanpa file resource / img.py
#  "CUR" diganti dengan warna saat render.
# ─────────────────────────────────────────────────────────────────────────────
ICON_BODIES = {
    "open": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "save": '<path d="M5 3h11l3 3v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/>'
            '<path d="M7 3v5h8V3"/><path d="M7 21v-7h10v7"/>',
    "find": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "replace": '<path d="M4 8h13l-3-3"/><path d="M20 16H7l3 3"/>',
    "zoom_in": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5M11 8v6M8 11h6"/>',
    "zoom_out": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5M8 11h6"/>',
    "picker": '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/>',
    "symbol": '<path d="M5 20h4v-2.2A7 7 0 1 1 15 17.8V20h4"/>',
    "weird": '<path d="m3 18 5-12 5 12M5 14h6"/><circle cx="18" cy="15" r="3"/><path d="M21 12v6"/>',
    "add": '<circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/>',
    "palette": '<circle cx="12" cy="12" r="9"/>'
               '<circle cx="8.5" cy="10.5" r="1" fill="CUR"/><circle cx="12" cy="7.8" r="1" fill="CUR"/>'
               '<circle cx="15.5" cy="10.5" r="1" fill="CUR"/>',
    "lyricolor": '<circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 1 0 18z" fill="CUR"/>',
    "kan2rom": '<path d="M4 6h9M8.5 4v2M6 6c0 4 3 7 6 8M12 6c0 3-3 7-7 9"/>'
               '<path d="m13 20 4-9 4 9M14.5 17h5"/>',
    "display": '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "sidebar_left": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/>',
    "sidebar_right": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M15 4v16"/>',
    "folder_big": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "copy": '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h8"/>',
    "font": '<path d="M4 7V4h16v3M9 20h6M12 4v16"/>',
    "keyboard": '<rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M7 14h10"/>',
    "lines": '<path d="M4 6h16M4 12h10M4 18h13"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "reset": '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>',
    "chevron_up": '<path d="m6 15 6-6 6 6"/>',
    "chevron_down": '<path d="m6 9 6 6 6-6"/>',
    "chevron_right": '<path d="m9 6 6 6-6 6"/>',
    "jutsu_editor": '<rect x="3" y="3" width="18" height="6" rx="1.5"/><path d="M7 13h10M7 16.5h6"/><path d="M3 20.5h18"/>',
    "wand": '<path d="m4 20 11-11"/><path d="m14 4 1 2 2 1-2 1-1 2-1-2-2-1 2-1zM19 12l.7 1.3L21 14l-1.3.7L19 16l-.7-1.3L17 14l1.3-.7z"/>',
    "chart_file": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M9 13h6M9 17h4"/>',
    "live_preview": '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>'
                    '<path d="M10.5 8v5l4-2.5z" fill="CUR"/>',
    "volume": '<path d="M4 9v6h4l5 4V5L8 9z"/>'
              '<path d="M16 8.5a5 5 0 0 1 0 7M18.5 6a8 8 0 0 1 0 12"/>',
    "volume_mute": '<path d="M4 9v6h4l5 4V5L8 9z"/><path d="m16 9 5 6M21 9l-5 6"/>',
    "play": '<path d="M7 4.5v15l12-7.5z" fill="CUR"/>',
    "pause": '<rect x="6" y="5" width="4" height="14" rx="1" fill="CUR"/>'
             '<rect x="14" y="5" width="4" height="14" rx="1" fill="CUR"/>',
    "stop": '<rect x="6" y="6" width="12" height="12" rx="2" fill="CUR"/>',
}


def render_svg(body: str, color: str, px: int, stroke: float = 1.8) -> QPixmap:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round">{body.replace("CUR", color)}</svg>'
    )
    pm = QPixmap(px, px)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    QSvgRenderer(QByteArray(svg.encode("utf-8"))).render(painter)
    painter.end()
    return pm


_icon_cache: dict = {}


def resolve_color(spec: str) -> str:
    """Nama token ('ACCENT') → warna tema aktif; selain itu dianggap warna literal ('#ffc78a')."""
    return get_active_theme().get(spec, spec)


def icon(name: str, normal: str = "DIM", hover: str = "TEXT",
         on: str = "ACCENT", disabled: str = "FAINT") -> QIcon:
    """QIcon multi-state: normal / hover(Active) / checked(On) / disabled.

    Tiap warna boleh nama token (diselesaikan terhadap tema aktif SAAT DIPANGGIL) atau hex literal."""
    normal, hover, on, disabled = (resolve_color(c) for c in (normal, hover, on, disabled))
    key = (name, normal, hover, on, disabled)
    if key in _icon_cache:
        return _icon_cache[key]
    body, px = ICON_BODIES[name], 64
    ic = QIcon()
    ic.addPixmap(render_svg(body, normal, px), QIcon.Mode.Normal, QIcon.State.Off)
    ic.addPixmap(render_svg(body, hover, px), QIcon.Mode.Active, QIcon.State.Off)
    ic.addPixmap(render_svg(body, on, px), QIcon.Mode.Normal, QIcon.State.On)
    ic.addPixmap(render_svg(body, on, px), QIcon.Mode.Active, QIcon.State.On)
    ic.addPixmap(render_svg(body, disabled, px), QIcon.Mode.Disabled, QIcon.State.Off)
    ic.addPixmap(render_svg(body, disabled, px), QIcon.Mode.Disabled, QIcon.State.On)
    _icon_cache[key] = ic
    return ic


def icon_pixmap(name: str, color: str, size: int) -> QPixmap:
    """``color``: nama token atau hex literal."""
    return render_svg(ICON_BODIES[name], resolve_color(color), size * 2).scaled(
        size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)


# ─────────────────────────────────────────────────────────────────────────────
#  Binding ikon/pixmap bertema: dibuat ulang otomatis saat tema berganti
#  (QIcon/QPixmap adalah gambar statis — tidak ikut berubah lewat stylesheet).
# ─────────────────────────────────────────────────────────────────────────────
_bindings: list = []        # (weakref target, nama setter, factory)


def bind_themed(target, setter: str, factory: Callable[[], object]) -> None:
    """Panggil ``target.<setter>(factory())`` sekarang dan setiap kali ``refresh_bound()`` jalan.

    ``factory`` tidak boleh menangkap ``target`` (agar tidak ada referensi melingkar); target
    dipegang weakref, jadi objek yang sudah dihapus otomatis dilepas."""
    getattr(target, setter)(factory())
    _bindings.append((weakref.ref(target), setter, factory))


def bind_icon(target, setter: str, name: str, normal: str = "DIM", hover: str = "TEXT",
              on: str = "ACCENT", disabled: str = "FAINT") -> None:
    bind_themed(target, setter, lambda: icon(name, normal, hover, on, disabled))


def bind_pixmap(target, setter: str, name: str, color: str, size: int) -> None:
    bind_themed(target, setter, lambda: icon_pixmap(name, color, size))


def refresh_bound() -> None:
    """Bangun ulang semua ikon/pixmap terikat dengan tema aktif. Dipanggil ThemeManager."""
    _icon_cache.clear()
    alive = []
    for ref, setter, factory in _bindings:
        target = ref()
        if target is None:
            continue
        try:
            getattr(target, setter)(factory())
        except RuntimeError:                  # objek C++ sudah dihapus
            continue
        alive.append((ref, setter, factory))
    _bindings[:] = alive
