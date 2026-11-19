"""Timing Engine — konversi tick chart ↔ detik, dengan peta tempo piecewise.

Murni Python (tanpa GUI). Semua perhitungan waktu musikal untuk Live Lyrics Preview ada di sini;
GUI/renderer tidak boleh menghitung timing sendiri.

Rumus per segmen tempo konstan (spesifikasi .chart)::

    Δt = (Δtick / resolution) * (60 / BPM)

Nilai BPM di chart disimpan sebagai BPM × 1000 (``B 150325`` = 150.325 BPM). Engine menyimpan nilai
integer itu apa adanya (``milli_bpm``) supaya BPM pecahan tidak kehilangan presisi.

Aturan yang dipakai (semuanya terdokumentasi, bukan tebakan):

* Marker tempo di tick 0 menentukan tempo awal. Jika tidak ada, dipakai **120 BPM** — aturan default
  format .chart (Guitar Game Chart Formats, bagian SyncTrack → Tempos).
* Marker diurutkan stabil berdasarkan tick. Bila beberapa marker berada di tick yang sama, yang
  **terakhir** (urutan file) menang, dan peringatan dicatat di ``warnings``.
* Marker tidak valid (tick < 0, BPM ≤ 0, bukan integer) dilewati dan dicatat di ``warnings``;
  engine tidak pernah melempar exception hanya karena data sync track jelek.
* ``offset_seconds`` (``Offset`` dari ``[Song]``) **tidak** ikut dalam matematika tick. Ia hanya
  dipakai oleh ``chart_to_audio_seconds`` / ``audio_to_chart_seconds``.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from fractions import Fraction
from math import isfinite
from typing import Iterable, Union

DEFAULT_MILLI_BPM = 120_000          # 120 BPM — default format .chart bila tick 0 tidak punya marker


@dataclass(frozen=True, slots=True)
class TempoEvent:
    """Satu marker tempo ``<tick> = B <milli_bpm>`` dari ``[SyncTrack]``.

    Attributes:
        tick:      Posisi marker (tick).
        milli_bpm: Nilai mentah chart = BPM × 1000 (``100000`` → 100 BPM).
    """

    tick: int
    milli_bpm: int

    @property
    def bpm(self) -> float:
        return self.milli_bpm / 1000.0


TempoInput = Union[TempoEvent, tuple[int, int]]          # tuple = (tick, milli_bpm)


class TimingEngine:
    """Peta tempo yang sudah diproses sebelumnya + lookup biner.

    Alur: ``load_tempo_map()`` sekali per chart (O(n log n)), lalu ``tick_to_seconds`` /
    ``seconds_to_tick`` / ``get_tempo_at_tick`` masing-masing O(log n) tanpa alokasi objek.
    """

    def __init__(self) -> None:
        self._resolution = 0
        self._ticks: list[int] = []              # tick awal tiap segmen (naik tegas)
        self._milli: list[int] = []              # milli-BPM tiap segmen
        self._start_seconds: list[float] = []    # waktu (detik) awal tiap segmen — kumulatif
        self._sec_per_tick: list[float] = []     # detik per tick tiap segmen
        self._offset_seconds = 0.0
        self.warnings: list[str] = []

    # ── konstruksi ───────────────────────────────────────────────────────
    def load_tempo_map(
        self,
        resolution: int,
        tempo_events: Iterable[TempoInput],
        *,
        offset_seconds: float = 0.0,
    ) -> None:
        """Bangun peta tempo.

        Args:
            resolution:   Tick per not seperempat (dibaca dinamis dari ``[Song]``; tidak di-hardcode).
            tempo_events: ``TempoEvent`` atau tuple ``(tick, milli_bpm)``; boleh tidak berurutan.
            offset_seconds: ``Offset`` chart (detik); hanya dipakai konversi chart↔audio.

        Raises:
            ValueError: jika *resolution* bukan integer > 0 atau *offset_seconds* tidak finit.
        """
        if isinstance(resolution, bool) or not isinstance(resolution, int) or resolution <= 0:
            raise ValueError(f"resolution must be an integer > 0, got: {resolution!r}")
        if not isfinite(offset_seconds):
            raise ValueError(f"offset_seconds must be finite, got: {offset_seconds!r}")

        warnings: list[str] = []
        events: list[tuple[int, int]] = []
        for raw in tempo_events:
            parsed = self._coerce(raw)
            if parsed is None:
                warnings.append(f"Tempo marker ignored (invalid): {raw!r}")
            else:
                events.append(parsed)

        events.sort(key=lambda e: e[0])          # stabil → urutan file dipertahankan untuk tick sama

        # Tick sama → yang terakhir menang.
        merged: list[tuple[int, int]] = []
        for tick, milli in events:
            if merged and merged[-1][0] == tick:
                warnings.append(
                    f"Duplicate tempo marker at tick {tick}: using {milli / 1000:g} BPM "
                    f"(replacing {merged[-1][1] / 1000:g} BPM)."
                )
                merged[-1] = (tick, milli)
            else:
                merged.append((tick, milli))

        if not merged or merged[0][0] != 0:
            if not merged:
                warnings.append("No tempo markers; using the default 120 BPM.")
            else:
                warnings.append("No tempo marker at tick 0; using the default 120 BPM.")
            merged.insert(0, (0, DEFAULT_MILLI_BPM))

        # Akumulasi eksak dengan Fraction supaya tidak ada drift pada lagu dengan banyak segmen;
        # hasil akhirnya disimpan sebagai float untuk lookup cepat.
        ticks: list[int] = []
        milli_list: list[int] = []
        starts: list[float] = []
        spt: list[float] = []
        cumulative = Fraction(0)
        for i, (tick, milli) in enumerate(merged):
            seconds_per_tick = Fraction(60_000, milli * resolution)     # 60 / (BPM * resolution)
            if i:
                prev_tick, prev_milli = merged[i - 1]
                cumulative += (tick - prev_tick) * Fraction(60_000, prev_milli * resolution)
            ticks.append(tick)
            milli_list.append(milli)
            starts.append(float(cumulative))
            spt.append(float(seconds_per_tick))

        # Commit atomik: state lama tidak setengah-terganti bila ada error di atas.
        self._resolution = resolution
        self._ticks = ticks
        self._milli = milli_list
        self._start_seconds = starts
        self._sec_per_tick = spt
        self._offset_seconds = float(offset_seconds)
        self.warnings = warnings

    @classmethod
    def from_chart_info(cls, info) -> "TimingEngine":
        """Bangun dari ``core.preview.chart_info.ChartInfo`` (duck-typed: song + tempo_events)."""
        engine = cls()
        engine.load_tempo_map(
            info.song.resolution,
            info.tempo_events,
            offset_seconds=info.song.offset_seconds,
        )
        return engine

    @staticmethod
    def _coerce(raw: TempoInput) -> tuple[int, int] | None:
        try:
            if isinstance(raw, TempoEvent):
                tick, milli = raw.tick, raw.milli_bpm
            else:
                tick, milli = raw
        except (TypeError, ValueError):
            return None
        if isinstance(tick, bool) or isinstance(milli, bool):
            return None
        if not isinstance(tick, int) or not isinstance(milli, int):
            return None
        if tick < 0 or milli <= 0:
            return None
        return tick, milli

    # ── state ────────────────────────────────────────────────────────────
    @property
    def is_loaded(self) -> bool:
        return self._resolution > 0

    @property
    def resolution(self) -> int:
        self._require_loaded()
        return self._resolution

    @property
    def offset_seconds(self) -> float:
        return self._offset_seconds

    @property
    def tempo_events(self) -> tuple[TempoEvent, ...]:
        """Peta tempo efektif (sudah dinormalisasi: terurut, tanpa duplikat, selalu mulai di tick 0)."""
        self._require_loaded()
        return tuple(TempoEvent(t, m) for t, m in zip(self._ticks, self._milli))

    def _require_loaded(self) -> None:
        if not self._resolution:
            raise RuntimeError("TimingEngine is not loaded: call load_tempo_map() first.")

    # ── konversi ─────────────────────────────────────────────────────────
    def tick_to_seconds(self, tick: float) -> float:
        """Waktu chart (detik sejak tick 0) untuk *tick*.

        Tick negatif diekstrapolasi dengan tempo segmen pertama (berguna untuk pre-roll).
        """
        self._require_loaded()
        i = bisect_right(self._ticks, tick) - 1
        if i < 0:
            i = 0
        return self._start_seconds[i] + (tick - self._ticks[i]) * self._sec_per_tick[i]

    def seconds_to_tick(self, seconds: float) -> float:
        """Kebalikan ``tick_to_seconds``; hasil float (boleh pecahan)."""
        self._require_loaded()
        i = bisect_right(self._start_seconds, seconds) - 1
        if i < 0:
            i = 0
        return self._ticks[i] + (seconds - self._start_seconds[i]) / self._sec_per_tick[i]

    def get_tempo_at_tick(self, tick: float) -> float:
        """BPM yang berlaku di *tick* (marker di tick itu sendiri sudah berlaku)."""
        self._require_loaded()
        i = bisect_right(self._ticks, tick) - 1
        if i < 0:
            i = 0
        return self._milli[i] / 1000.0

    # ── offset chart ↔ audio ─────────────────────────────────────────────
    def chart_to_audio_seconds(self, chart_seconds: float) -> float:
        """Posisi audio untuk waktu chart tertentu.

        Menurut spesifikasi ``Offset`` ("nilai lebih tinggi membuat audio mulai lebih awal"),
        ``audio = chart + offset``. Clone Hero memakai ``Offset`` ini (termasuk nilai negatif sejak v1.1).
        """
        return chart_seconds + self._offset_seconds

    def audio_to_chart_seconds(self, audio_seconds: float) -> float:
        """Kebalikan ``chart_to_audio_seconds``."""
        return audio_seconds - self._offset_seconds
