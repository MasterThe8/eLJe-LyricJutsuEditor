"""Pembaca metadata ``[Song]`` dan marker tempo ``[SyncTrack]``.

Chart engine yang ada (``core.chart``) menyimpan section ``[Song]`` dan ``[SyncTrack]`` sebagai
string mentah di ``ChartDocument.song`` / ``ChartDocument.sync_track`` dan belum mengurai isinya.
Modul ini hanya **membaca** string itu — chart engine tidak diubah.

Murni Python (tanpa GUI).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from math import isfinite

from core.preview.timing_engine import TempoEvent

# Resolusi cadangan HANYA bila [Song] tidak punya Resolution yang valid. Spesifikasi menyebut
# Resolution "wajib"; 192 adalah konvensi umum (Moonscraper/Feedback). Pemakaian cadangan selalu
# ditandai lewat ``ChartSongInfo.resolution_assumed`` + warning supaya UI bisa memberi tahu pengguna.
FALLBACK_RESOLUTION = 192

_ENTRY_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*(.*?)\s*$")
_TICK_EVENT_RE = re.compile(r"^\s*(\d+)\s*=\s*([A-Za-z]+)\b\s*(.*?)\s*$")


@dataclass(frozen=True)
class ChartSongInfo:
    """Metadata ``[Song]`` yang relevan untuk preview."""

    resolution: int = FALLBACK_RESOLUTION
    resolution_assumed: bool = True          # True → Resolution tidak ada/tidak valid, dipakai cadangan
    music_stream: str | None = None          # nama file persis seperti di chart (None bila tidak ada)
    offset_seconds: float = 0.0              # [Song] Offset (detik); audio = chart + offset
    name: str | None = None
    artist: str | None = None
    properties: dict[str, str] = field(default_factory=dict)   # semua entri apa adanya (kunci lower-case)
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ChartInfo:
    """Gabungan metadata lagu + marker tempo, siap diberikan ke ``TimingEngine``."""

    song: ChartSongInfo
    tempo_events: tuple[TempoEvent, ...] = ()
    warnings: tuple[str, ...] = ()           # gabungan warning song + synctrack


# ─────────────────────────────────────────────────────────────────────────────
#  [Song]
# ─────────────────────────────────────────────────────────────────────────────

def _unquote(value: str) -> tuple[str, bool]:
    """Buang HANYA tanda kutip pembuka & penutup paling luar (saran spesifikasi: .chart tidak
    punya escape, jadi kutip di tengah nilai dibiarkan). Mengembalikan ``(nilai, was_quoted)``."""
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1], True
    return value, False


def _parse_song_entries(song_section: str) -> tuple[dict[str, tuple[str, bool]], list[str]]:
    entries: dict[str, tuple[str, bool]] = {}
    warnings: list[str] = []
    for line in (song_section or "").splitlines():
        m = _ENTRY_RE.match(line)
        if not m:
            continue                                 # "[Song]", "{", "}", baris kosong, dll.
        key = m.group(1).lower()
        if key in entries:
            warnings.append(f"[Song] duplicate entry '{m.group(1)}': the first value is used.")
            continue
        entries[key] = _unquote(m.group(2))
    return entries, warnings


def parse_song_section(song_section: str) -> ChartSongInfo:
    """Urai teks section ``[Song]`` (boleh dengan/ tanpa header & kurung kurawal)."""
    entries, warnings = _parse_song_entries(song_section)
    props = {k: v for k, (v, _q) in entries.items()}

    # Resolution -------------------------------------------------------------
    resolution = FALLBACK_RESOLUTION
    assumed = True
    if "resolution" not in entries:
        warnings.append(f"[Song] has no Resolution; using {FALLBACK_RESOLUTION}.")
    else:
        raw = entries["resolution"][0].strip()
        try:
            parsed = int(raw)
        except ValueError:
            parsed = 0
        if parsed > 0:
            resolution, assumed = parsed, False
        else:
            warnings.append(f"Resolution is invalid ({raw!r}); using {FALLBACK_RESOLUTION}.")

    # MusicStream ------------------------------------------------------------
    music_stream: str | None = None
    if "musicstream" in entries:
        value, quoted = entries["musicstream"]
        # Spesifikasi: tipe "file path" = path dalam kutip, atau `None` (tanpa kutip) bila kosong.
        if value.strip() and not (not quoted and value.strip().lower() == "none"):
            music_stream = value

    # Offset -----------------------------------------------------------------
    offset = 0.0
    if "offset" in entries:
        raw = entries["offset"][0].strip()
        try:
            offset = float(raw)
            if not isfinite(offset):
                raise ValueError(raw)
        except ValueError:
            offset = 0.0
            warnings.append(f"Offset is invalid ({raw!r}); using 0.")

    return ChartSongInfo(
        resolution=resolution,
        resolution_assumed=assumed,
        music_stream=music_stream,
        offset_seconds=offset,
        name=props.get("name"),
        artist=props.get("artist"),
        properties=props,
        warnings=tuple(warnings),
    )


# ─────────────────────────────────────────────────────────────────────────────
#  [SyncTrack]
# ─────────────────────────────────────────────────────────────────────────────

def parse_sync_track(sync_section: str) -> tuple[tuple[TempoEvent, ...], tuple[str, ...]]:
    """Ambil marker tempo (``B``) dari teks section ``[SyncTrack]``.

    Marker ``TS`` (birama) dan ``A`` (anchor editor) tidak memengaruhi timing playback dan dilewati.
    Urutan file dipertahankan; normalisasi (sort, duplikat, default 120 BPM) dilakukan ``TimingEngine``.
    Mengembalikan ``(tempo_events, warnings)``.
    """
    events: list[TempoEvent] = []
    warnings: list[str] = []
    for line in (sync_section or "").splitlines():
        m = _TICK_EVENT_RE.match(line)
        if not m or m.group(2).upper() != "B":
            continue
        tick = int(m.group(1))
        value = m.group(3).strip()
        if not value.isdigit() or int(value) <= 0:
            warnings.append(f"Tempo marker at tick {tick} ignored (invalid BPM value: {value!r}).")
            continue
        events.append(TempoEvent(tick, int(value)))
    return tuple(events), tuple(warnings)


# ─────────────────────────────────────────────────────────────────────────────
#  Gabungan
# ─────────────────────────────────────────────────────────────────────────────

def read_chart_info(doc) -> ChartInfo:
    """Baca metadata dari ``ChartDocument`` (duck-typed: butuh atribut ``song`` & ``sync_track``)."""
    return read_chart_info_from_sections(
        getattr(doc, "song", "") or "",
        getattr(doc, "sync_track", "") or "",
    )


def read_chart_info_from_sections(song_section: str, sync_section: str) -> ChartInfo:
    song = parse_song_section(song_section)
    tempos, sync_warnings = parse_sync_track(sync_section)
    return ChartInfo(song=song, tempo_events=tempos, warnings=song.warnings + sync_warnings)
