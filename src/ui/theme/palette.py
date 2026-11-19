"""Palet gelap QApplication, dibangun dari token tema aktif."""
from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from ui.theme.tokens import get_active_theme


def build_palette() -> QPalette:
    t = get_active_theme()
    pal = QPalette()
    R, G = QPalette.ColorRole, QPalette.ColorGroup
    for role, key in (
        (R.Window, "CHROME"), (R.WindowText, "TEXT"),
        (R.Base, "EDITOR"), (R.AlternateBase, "PANEL"),
        (R.Text, "TEXT"), (R.Button, "RAISED"), (R.ButtonText, "TEXT"),
        (R.ToolTipBase, "RAISED"), (R.ToolTipText, "TEXT"),
        (R.Highlight, "SELECTION"), (R.HighlightedText, "SELECTION_TEXT"),
        (R.PlaceholderText, "FAINT"), (R.Link, "ACCENT"),
    ):
        pal.setColor(role, QColor(t[key]))
    for role in (R.Text, R.ButtonText, R.WindowText):
        pal.setColor(G.Disabled, role, QColor(t["FAINT"]))
    return pal


def apply_dark_palette(app: QApplication) -> None:
    """Terapkan palet dari tema aktif. Aman dipanggil ulang setiap tema berganti."""
    app.setPalette(build_palette())
