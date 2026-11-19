"""Helper kecil pembuat potongan HTML berwarna untuk label dan pratinjau."""
from __future__ import annotations

import html

from PySide6.QtGui import QColor


def span(color: str, text: str) -> str:
    return f"<span style='color:{color}'>{html.escape(text)}</span>"


def event_line_html(colors: dict, pos: str, event: str, text: str = "") -> str:
    """Satu baris event berwarna, meniru LyricHighlighter. Dipakai pratinjau setting."""
    value = span(colors["value"], '"') + span(colors["eventname"], event)
    if text:
        value += span(colors["value"], " " + text)
    value += span(colors["value"], '"')
    return f"<pre style='margin:0'>{span(colors['position'], pos)} = E {value}</pre>"


# ─────────────────────────────────────────────────────────────────────────────
#  About
# ─────────────────────────────────────────────────────────────────────────────
def gradient_html(text: str, stops: list[str]) -> str:
    """Teks per-huruf berwarna gradien (pengganti deretan <b style=color> manual)."""
    cols = [QColor(c) for c in stops]
    n, out = len(text), []
    for i, ch in enumerate(text):
        if ch == " ":
            out.append(" ")
            continue
        t = (i / max(n - 1, 1)) * (len(cols) - 1)
        a = min(int(t), len(cols) - 2)
        f = t - a
        c0, c1 = cols[a], cols[a + 1]
        c = QColor(int(c0.red() + (c1.red() - c0.red()) * f),
                   int(c0.green() + (c1.green() - c0.green()) * f),
                   int(c0.blue() + (c1.blue() - c0.blue()) * f))
        out.append(f"<b style='color:{c.name()}'>{html.escape(ch)}</b>")
    return "".join(out)
