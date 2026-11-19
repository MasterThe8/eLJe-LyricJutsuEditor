"""Event Scheduler — dari waktu playback menjadi *state* lirik.

Murni Python (tanpa GUI). Scheduler adalah fungsi murni dari ``waktu`` → ``LyricState``; ia tidak
menyimpan posisi sebelumnya. Akibatnya pause, resume, seek maju/mundur, loop, dan lompat ke tengah
lagu otomatis benar: state selalu direkonstruksi dari waktu, tidak pernah diakumulasi.

Yang dilaporkan scheduler adalah **fakta yang bisa diukur** dari chart. Keputusan visual — kapan
preview baris berikutnya muncul, berapa lama transisi/animasi, apakah baris yang sudah selesai
masih ditampilkan sebentar — sengaja TIDAK ditetapkan di sini, karena perilaku persis Clone Hero
untuk hal itu tidak terdokumentasi. Renderer memutuskannya berdasarkan ``time_until_next_phrase``,
``time_since_phrase_end``, dan ``phase``.

Semantik waktu (semua dalam detik *chart*, lihat ``TimingEngine.audio_to_chart_seconds`` untuk offset):

* Phrase aktif untuk ``start_time <= t < end_time`` (setengah terbuka). Phrase terakhir tanpa
  akhir (``end_time is None``) aktif tanpa batas; scheduler tidak mengarang akhirnya.
* Suku kata "sudah lewat" bila ``timestamp <= t``. Beberapa suku kata di tick yang sama lewat
  bersamaan; ``active_lyric`` adalah yang terakhir di antaranya.
* Phrase kosong (tanpa lirik) tidak pernah menjadi phrase aktif/berikutnya.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from enum import Enum

from core.preview.lyrics_parser import LyricEvent, ParsedLyrics, PreviewPhrase
from core.preview.timing_engine import TimingEngine


class SchedulePhase(str, Enum):
    NO_LYRICS = "no_lyrics"          # chart tidak punya phrase berisi lirik
    BEFORE_FIRST = "before_first"    # sebelum phrase pertama dimulai (termasuk waktu negatif)
    ACTIVE = "active"                # berada di dalam sebuah phrase
    GAP = "gap"                      # di antara dua phrase (phrase sebelumnya sudah ditutup)
    AFTER_LAST = "after_last"        # setelah phrase terakhir yang ditutup eksplisit


@dataclass(frozen=True, slots=True)
class LyricState:
    """Snapshot lirik pada satu waktu."""

    time: float
    phase: SchedulePhase
    phrase: PreviewPhrase | None             # phrase aktif (hanya saat ACTIVE)
    previous_phrase: PreviewPhrase | None    # phrase terakhir yang sudah dimulai selain yang aktif
    next_phrase: PreviewPhrase | None        # phrase pertama yang belum dimulai
    sung_count: int                          # jumlah suku kata di phrase aktif yang sudah lewat
    active_lyric: LyricEvent | None          # suku kata terakhir yang sudah lewat (None = belum ada)
    phrase_progress: float | None            # 0..1 dalam phrase aktif; None bila akhirnya tidak diketahui
    time_until_next_phrase: float | None     # detik sampai next_phrase mulai (None bila tidak ada)
    time_since_phrase_end: float | None      # detik sejak previous_phrase berakhir (GAP/AFTER_LAST)

    @property
    def key(self) -> tuple[SchedulePhase, int | None, int]:
        """Identitas perubahan visual diskret: UI hanya perlu repaint bila ``key`` berubah."""
        return (self.phase, None if self.phrase is None else self.phrase.phrase_id, self.sung_count)


_EMPTY_STATE_FIELDS = dict(phrase=None, previous_phrase=None, next_phrase=None, sung_count=0,
                           active_lyric=None, phrase_progress=None, time_until_next_phrase=None,
                           time_since_phrase_end=None)


class LyricScheduler:
    """Indeks lookup biner atas ``ParsedLyrics``; dibangun sekali per chart, query O(log n)."""

    def __init__(self, parsed: ParsedLyrics, timing: TimingEngine | None = None) -> None:
        self._timing = timing
        # Hanya phrase berisi lirik yang bisa ditampilkan; urut menurut start (parser menjamin non-overlap).
        self._phrases: list[PreviewPhrase] = [p for p in parsed.phrases if not p.is_empty]
        self._starts: list[float] = [p.start_time for p in self._phrases]
        self._lyric_times: list[list[float]] = [[l.timestamp for l in p.lyrics] for p in self._phrases]

    # ── info ─────────────────────────────────────────────────────────────
    @property
    def phrases(self) -> tuple[PreviewPhrase, ...]:
        """Phrase yang bisa ditampilkan (tanpa phrase kosong), urut waktu."""
        return tuple(self._phrases)

    def __len__(self) -> int:
        return len(self._phrases)

    # ── query ────────────────────────────────────────────────────────────
    def state_at(self, seconds: float) -> LyricState:
        """State pada waktu chart *seconds* (detik dari tick 0, tanpa offset audio)."""
        phrases = self._phrases
        if not phrases:
            return LyricState(seconds, SchedulePhase.NO_LYRICS, **_EMPTY_STATE_FIELDS)

        i = bisect_right(self._starts, seconds) - 1          # phrase terakhir yang sudah dimulai
        if i < 0:
            return LyricState(seconds, SchedulePhase.BEFORE_FIRST, **{
                **_EMPTY_STATE_FIELDS,
                "next_phrase": phrases[0],
                "time_until_next_phrase": self._starts[0] - seconds,
            })

        current = phrases[i]
        following = phrases[i + 1] if i + 1 < len(phrases) else None
        until_next = None if following is None else following.start_time - seconds
        end_time = current.end_time

        if end_time is None or seconds < end_time:           # ACTIVE
            sung = bisect_right(self._lyric_times[i], seconds)
            progress = None
            if end_time is not None and end_time > current.start_time:
                progress = (seconds - current.start_time) / (end_time - current.start_time)
            return LyricState(
                time=seconds,
                phase=SchedulePhase.ACTIVE,
                phrase=current,
                previous_phrase=phrases[i - 1] if i > 0 else None,
                next_phrase=following,
                sung_count=sung,
                active_lyric=current.lyrics[sung - 1] if sung else None,
                phrase_progress=progress,
                time_until_next_phrase=until_next,
                time_since_phrase_end=None,
            )

        # Phrase sudah ditutup eksplisit sebelum phrase berikutnya mulai → jeda.
        return LyricState(
            time=seconds,
            phase=SchedulePhase.GAP if following is not None else SchedulePhase.AFTER_LAST,
            phrase=None,
            previous_phrase=current,
            next_phrase=following,
            sung_count=0,
            active_lyric=None,
            phrase_progress=None,
            time_until_next_phrase=until_next,
            time_since_phrase_end=seconds - end_time,
        )

    def state_at_tick(self, tick: float) -> LyricState:
        """Pintasan: state pada posisi *tick* (butuh ``timing``)."""
        return self.state_at(self._require_timing().tick_to_seconds(tick))

    def state_at_audio(self, audio_seconds: float) -> LyricState:
        """State untuk posisi audio (detik di file audio). Menerapkan ``Offset`` chart lebih dulu."""
        return self.state_at(self._require_timing().audio_to_chart_seconds(audio_seconds))

    def _require_timing(self) -> TimingEngine:
        if self._timing is None:
            raise RuntimeError("LyricScheduler was created without a TimingEngine; tick/audio conversion is unavailable.")
        return self._timing
