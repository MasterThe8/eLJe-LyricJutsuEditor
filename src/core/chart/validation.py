"""Validasi struktur satu baris script event di ``[Events]``.

Bentuk baris yang benar::

    <tick/position> = E "<event_name> <input (opsional)>"

Contoh benar::

    768 = E "phrase_start"
    864 = E "lyric the"
    960 = E "lyric <color=#FF5E9C>light</color>"

Contoh salah (dan alasannya)::

    123 = E "lyric asd      → tanda " penutup tidak ada
    123 = "phrase_start"    → 'E' tidak ada setelah '='
    abc = E "lyric x"       → tick bukan bilangan bulat

Murni Python (tanpa GUI), tidak mengubah ``core.chart.events`` (parser lama yang sengaja longgar).
Modul ini hanya MEMERIKSA bentuk baris; makna event (mis. apakah ``lyric`` ada di dalam phrase)
bukan urusannya. Nama event tidak dibatasi ke daftar tertentu karena chart boleh memuat event apa
saja (``section``, ``end``, ``solo``, …); yang diperiksa hanya bahwa nama itu ada.
"""
from __future__ import annotations

import re

_TICK_RE = re.compile(r"[0-9]+")
_EVENT_NAME_RE = re.compile(r'[^\s"]+')       # satu kata tanpa spasi / tanda kutip


def _found(tail: str) -> str:
    """Yang ditemukan menggantikan 'E' untuk pesan error: satu kata bila diawali huruf (``e``, ``Event``), selain itu satu karakter."""
    return tail.split(None, 1)[0] if tail[0].isalpha() else tail[0]


def check_event_line(line: str) -> str | None:
    """Periksa satu baris event.

    Returns:
        ``None`` bila baris valid (baris kosong / hanya spasi juga dianggap valid, itu bukan script),
        atau pesan singkat yang menjelaskan kesalahan pertama yang ditemukan.
    """
    text = line.strip()
    if not text:
        return None

    # ── 1) <tick> = ─────────────────────────────────────────────────────────
    head, equals, tail = text.partition("=")
    if not equals:
        return "Missing '=' after the tick position"
    head = head.strip()
    if not head:
        return "Missing tick position before '='"
    if not _TICK_RE.fullmatch(head):
        return "Tick position must be a whole number (digits only)"

    # ── 2) E ────────────────────────────────────────────────────────────────
    tail = tail.lstrip()
    if not tail:
        return "Missing 'E' and the event text after '='"
    if not tail.startswith("E"):
        return f"Missing 'E' after '=' (found {_found(tail)!r})"
    after_e = tail[1:]
    if after_e and not after_e[0].isspace():
        if after_e[0] == '"':
            return "Missing space between 'E' and the opening quote"
        return f"Missing 'E' after '=' (found {_found(tail)!r})"     # mis. `Event "..."`

    # ── 3) "<event_name> <input>" ───────────────────────────────────────────
    body = after_e.strip()
    if not body:
        return "Missing event text after 'E'"
    if body[0] != '"':
        return 'Missing opening quote (") before the event name'
    if len(body) < 2 or body[-1] != '"':
        # Tanda kutip penutup harus karakter TERAKHIR di baris (lirik boleh memuat tanda kutip sendiri).
        if '"' in body[1:]:
            return 'Closing quote (") must be the last character on the line'
        return 'Missing closing quote (")'

    inner = body[1:-1]
    name = _EVENT_NAME_RE.match(inner)
    if name is None:
        return "Missing event name right after the opening quote"
    rest = inner[name.end():]
    if rest and not rest[0].isspace():
        return "Event name must be followed by a space and its input (or by the closing quote)"
    return None
