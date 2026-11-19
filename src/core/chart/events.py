"""Utilitas untuk memanipulasi event di section [Events].

Berisi fungsi-fungsi:
  - Sorting event berdasarkan posisi dan prioritas (migrasi dari ``event_sort``).
  - Parsing baris event individual.
  - Konversi event ke display text (untuk pratinjau lirik).

Logika dimigrasi dari:
  - ``main.py`` method ``event_sort()`` (baris 1018-1045)
  - ``main.py`` method ``toRichText()`` (baris 908-933)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
#  Data class untuk satu baris event
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ChartEvent:
    """Representasi terstruktur dari satu baris event .chart.

    Contoh baris: ``768 = E "lyric Hello"``
      - position  = ``768``
      - raw_data  = ``E "lyric Hello"``
      - name      = ``lyric``
      - value     = ``Hello``
    """

    position: int
    raw_data: str
    name: str
    value: str = ""

    @property
    def is_lyric(self) -> bool:
        return self.name == "lyric"

    @property
    def is_phrase_start(self) -> bool:
        return self.name == "phrase_start"

    @property
    def is_phrase_end(self) -> bool:
        return self.name == "phrase_end"

    @property
    def is_section(self) -> bool:
        return self.name == "section"

    def to_line(self) -> str:
        """Kembalikan sebagai baris teks .chart."""
        return f'{self.position} = E "{self.name}{" " + self.value if self.value else ""}"'


# ─────────────────────────────────────────────────────────────────────────────
#  Regex untuk parsing baris event
# ─────────────────────────────────────────────────────────────────────────────
_EVENT_RE = re.compile(
    r'^\s*(\d+)\s*=\s*E\s+"(\w+)(?:\s(.*?))?"?\s*$'
)


# ─────────────────────────────────────────────────────────────────────────────
#  Parsing
# ─────────────────────────────────────────────────────────────────────────────

def parse_event_line(line: str) -> Optional[ChartEvent]:
    """Parse satu baris event menjadi ChartEvent. Mengembalikan None jika format tidak cocok."""
    m = _EVENT_RE.match(line)
    if not m:
        return None
    position = int(m.group(1))
    name = m.group(2)
    value = m.group(3) or ""
    raw_data = line.split("=", 1)[1].strip() if "=" in line else ""
    return ChartEvent(position=position, raw_data=raw_data, name=name, value=value)


def parse_events_text(text: str) -> list[ChartEvent]:
    """Parse seluruh teks event body menjadi list ChartEvent.

    Baris yang tidak cocok format event dilewati.
    """
    events = []
    for line in text.splitlines():
        ev = parse_event_line(line)
        if ev is not None:
            events.append(ev)
    return events


# ─────────────────────────────────────────────────────────────────────────────
#  Sorting
# ─────────────────────────────────────────────────────────────────────────────

def sort_events(text: str, *, reverse: bool = True) -> str:
    """Urutkan baris-baris event berdasarkan posisi, dengan prioritas pada
    event ``lyric`` dan ``phrase_start``.

    Migrasi dari ``main.py:event_sort()``.

    Args:
        text:    Teks events body (multi-baris).
        reverse: Jika True, urutan descending (sesuai behavior asli).

    Returns:
        Teks yang sudah diurutkan.
    """
    lines = text.splitlines()

    def _sort_key(line: str) -> tuple[str, int]:
        parts = line.split(" = ", 1)
        if len(parts) != 2:
            return ("", 0)
        position = parts[0].strip()
        event_data = parts[1].strip().strip('E "').split(" ", 1)
        event_name = event_data[0]
        # Prioritas lebih tinggi (0) untuk lyric dan phrase_start
        priority = 0 if event_name in ("lyric", "phrase_start") else 1
        return (position, priority)

    sorted_lines = sorted(lines, key=_sort_key, reverse=reverse)
    return "\n".join(sorted_lines)


# ─────────────────────────────────────────────────────────────────────────────
#  Konversi ke teks lirik (untuk pratinjau Display Lyrics)
# ─────────────────────────────────────────────────────────────────────────────

def events_to_lyric_lines(text: str) -> list[str]:
    """Konversi teks event body menjadi baris-baris lirik untuk ditampilkan.

    Migrasi dari ``main.py:toRichText()`` (baris 908-933).

    Setiap ``phrase_start`` memulai baris baru. Event ``lyric`` digabung
    menjadi kata-kata, dengan ``-`` di akhir kata menandakan penyambungan
    suku kata (tanpa spasi).

    Args:
        text: Teks events body (multi-baris, hanya baris non-kosong diproses).

    Returns:
        List string, masing-masing satu baris lirik lengkap.
    """
    # Filter baris kosong
    lines = [line for line in text.splitlines() if line.strip()]

    result: list[str] = []
    current_line = ""

    for line in lines:
        ev = parse_event_line(line)
        if ev is None:
            continue

        if ev.is_phrase_start:
            if current_line:
                result.append(current_line.strip())
                current_line = ""

        elif ev.is_lyric:
            value = ev.value
            if "-" in value:
                # Suku kata yang disambung — tidak perlu spasi jika baris sebelumnya
                # sudah diakhiri dash
                if current_line and not current_line.endswith("-"):
                    current_line += " "
                current_line += value
            else:
                if current_line and not current_line.endswith("-"):
                    current_line += " "
                current_line += value

    if current_line:
        result.append(current_line.strip())

    return result
