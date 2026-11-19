"""Widget/factory kecil yang dipakai di banyak tempat."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from ui.theme import bind_icon


# ─────────────────────────────────────────────────────────────────────────────
#  Helper widget kecil
# ─────────────────────────────────────────────────────────────────────────────
def make_button(text: str, kind: str = "", icon_name: str | None = None) -> QPushButton:
    """kind: "" (default) | "primary" | "ghost"."""
    b = QPushButton(text)
    if kind:
        b.setObjectName(kind)
    if icon_name:
        if kind == "primary":                       # ikon gelap di atas latar aksen
            bind_icon(b, "setIcon", icon_name, "PRIMARY_TEXT", "PRIMARY_TEXT", "PRIMARY_TEXT", "FAINT")
        else:
            bind_icon(b, "setIcon", icon_name, "DIM", "TEXT", "DIM", "FAINT")
        b.setIconSize(QSize(16, 16))
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


class DoubleClickLabel(QLabel):
    """QLabel yang memancarkan ``double_clicked`` saat diklik ganda (tombol kiri).

    Sengaja tanpa kursor tangan / tooltip: dipakai sebagai pemicu fitur tersembunyi (mis. chip versi di status bar)."""

    double_clicked = Signal()

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)


def soft_wrap(lbl: QLabel, wrap: bool = True) -> QLabel:
    """Label yang lebarnya mengikuti kolom, bukan memaksa kolom melebar mengikuti teks.

    Tanpa ini, teks panjang (hint, lirik pengguna) membuat sizeHint label — dan akhirnya lebar dialog — ikut membesar.
    wrap=True  → teks membungkus ke baris berikutnya (untuk kalimat: hint, caption).
    wrap=False → teks tidak membungkus (untuk baris kode/event; pemotongan ditangani pemanggil).
    Urutan penting: setWordWrap dulu (QLabel menyalakan flag heightForWidth), lalu ubah policy horizontal saja.
    """
    if wrap:
        lbl.setWordWrap(True)
    policy = lbl.sizePolicy()
    policy.setHorizontalPolicy(QSizePolicy.Policy.Ignored)
    lbl.setSizePolicy(policy)
    return lbl


def field_label(text: str, name: str = "fieldLabel", wrap: bool = False) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName(name)
    if wrap:
        soft_wrap(lbl)
    return lbl


def divider(vertical: bool = False) -> QFrame:
    f = QFrame()
    f.setObjectName("vdivider" if vertical else "hdivider")
    return f


# ─────────────────────────────────────────────────────────────────────────────
#  Panel kiri: Song Chart Directory
# ─────────────────────────────────────────────────────────────────────────────
def panel_header(title: str, button: QWidget | None = None, hint: QLabel | None = None) -> QWidget:
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(16, 12, 10, 8)
    lay.setSpacing(8)
    t = QLabel(title)
    t.setObjectName("panelTitle")
    lay.addWidget(t)
    if hint is not None:
        lay.addWidget(hint, 1)
    else:
        lay.addStretch(1)
    if button is not None:
        lay.addWidget(button)
    return w


def tool_button(icon_name: str, tooltip: str):
    b = QToolButton()
    bind_icon(b, "setIcon", icon_name)
    b.setIconSize(QSize(18, 18))
    b.setToolTip(tooltip)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setAutoRaise(True)
    return b


def add_line_edit_icon(edit: QLineEdit, icon_name: str, position: QLineEdit.ActionPosition):
    """Ikon di dalam QLineEdit (aksi) yang ikut berganti warna saat tema berubah."""
    act = edit.addAction(QIcon(), position)
    bind_icon(act, "setIcon", icon_name)
    return act
