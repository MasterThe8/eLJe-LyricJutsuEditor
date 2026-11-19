"""Lyrics Parser — mengubah teks ``[Events]`` menjadi model phrase/lirik berstempel waktu.

Murni Python (tanpa GUI). Memakai ``core.chart.events.parse_events_text`` yang sudah ada untuk
mengurai baris event; modul ini hanya menambah logika phrase + timestamp dan tidak mengubah
parser lama.

Aturan phrase (spesifikasi Guitar Game Chart Formats → Lyrics):

* ``phrase_start`` memulai phrase baru; ``phrase_end`` sebelumnya **tidak wajib**. Jika phrase masih
  terbuka saat ``phrase_start`` berikutnya muncul, phrase itu berakhir *implisit* di tick
  ``phrase_start`` tersebut (``end_explicit=False``).
* ``phrase_end`` menutup phrase yang terbuka (``end_explicit=True``).
* Phrase terakhir tanpa ``phrase_end`` dibiarkan ``end_tick=None``; tidak ada akhir yang dikarang.
* ``phrase_start`` TIDAK harus sejajar dengan lirik pertama (contoh spesifikasi: start 576, lirik 768).
* Phrase kosong dipertahankan (``is_empty``) supaya penomoran ``phrase_id`` setia pada chart;
  scheduler/renderer yang memutuskan untuk melewatinya.

Lirik yang tidak berada di dalam phrase ("orphan") dan ``phrase_end`` liar tidak dibuang diam-diam
maupun dimasukkan ke phrase karangan: orphan disimpan di ``orphan_lyrics`` + warning.

Teks lirik dipertahankan persis (tanda hubung, tanda baca, tag ``<color>``/``<b>``, Unicode,
spasi di awal/akhir). Tidak ada pemecahan suku kata otomatis.

Urutan event: diurutkan **stabil** menurut tick, sehingga event di tick yang sama mengikuti urutan
file (``phrase_start`` lalu ``lyric`` seperti biasa). ``timestamp`` adalah waktu *chart* (detik dari
tick 0, tanpa ``Offset``); konversi ke posisi audio dilakukan lewat ``TimingEngine``.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core.chart.events import parse_events_text
from core.preview.timing_engine import TimingEngine


@dataclass(frozen=True, slots=True)
class LyricEvent:
    """Satu suku kata ``E "lyric <text>"``."""

    tick: int
    timestamp: float          # detik chart (dari tick 0), dihitung TimingEngine
    text: str                 # persis seperti di chart
    phrase_id: int            # -1 untuk lirik orphan
    index: int = 0            # urutan global di ParsedLyrics.lyrics (pemutus seri untuk tick sama)


@dataclass(frozen=True, slots=True)
class PreviewPhrase:
    """Satu phrase lirik (``phrase_start`` … ``phrase_end``/phrase berikutnya)."""

    phrase_id: int
    start_tick: int
    end_tick: int | None
    lyrics: tuple[LyricEvent, ...]
    start_time: float
    end_time: float | None
    end_explicit: bool = False    # True bila diakhiri phrase_end; False bila implisit / tanpa akhir

    @property
    def is_empty(self) -> bool:
        return not self.lyrics


@dataclass
class ParsedLyrics:
    """Hasil parsing: phrase berurutan + daftar lirik datar."""

    phrases: list[PreviewPhrase] = field(default_factory=list)
    lyrics: list[LyricEvent] = field(default_factory=list)          # hanya lirik di dalam phrase, urut tick
    orphan_lyrics: list[LyricEvent] = field(default_factory=list)   # lirik di luar phrase manapun
    warnings: list[str] = field(default_factory=list)


class _OpenPhrase:
    __slots__ = ("phrase_id", "start_tick", "lyrics")

    def __init__(self, phrase_id: int, start_tick: int) -> None:
        self.phrase_id = phrase_id
        self.start_tick = start_tick
        self.lyrics: list[LyricEvent] = []


def parse_lyrics(events_text: str, timing: TimingEngine) -> ParsedLyrics:
    """Bangun model lirik dari teks body ``[Events]``.

    Args:
        events_text: Isi body ``[Events]`` (mis. teks editor — bukan ``doc.events_body`` lama,
                     karena pengguna bisa mengedit tanpa menyimpan).
        timing:      ``TimingEngine`` yang sudah dimuat; dipakai menghitung semua timestamp.

    Event selain ``phrase_start`` / ``phrase_end`` / ``lyric`` (mis. ``section``, ``end``) diabaikan.
    """
    result = ParsedLyrics()
    if not events_text:
        return result

    events = parse_events_text(events_text)
    events.sort(key=lambda e: e.position)            # stabil: tick sama → urutan file

    current: _OpenPhrase | None = None
    next_id = 0

    def close(open_phrase: _OpenPhrase, end_tick: int | None, explicit: bool) -> None:
        result.phrases.append(PreviewPhrase(
            phrase_id=open_phrase.phrase_id,
            start_tick=open_phrase.start_tick,
            end_tick=end_tick,
            lyrics=tuple(open_phrase.lyrics),
            start_time=timing.tick_to_seconds(open_phrase.start_tick),
            end_time=None if end_tick is None else timing.tick_to_seconds(end_tick),
            end_explicit=explicit,
        ))

    for ev in events:
        if ev.is_phrase_start:
            if current is not None:
                close(current, ev.position, explicit=False)         # akhir implisit
            current = _OpenPhrase(next_id, ev.position)
            next_id += 1

        elif ev.is_phrase_end:
            if current is None:
                result.warnings.append(f"phrase_end at tick {ev.position} without phrase_start; ignored.")
            else:
                close(current, ev.position, explicit=True)
                current = None

        elif ev.is_lyric:
            if current is None:
                lyric = LyricEvent(ev.position, timing.tick_to_seconds(ev.position), ev.value, -1,
                                   len(result.orphan_lyrics))
                result.orphan_lyrics.append(lyric)
                result.warnings.append(
                    f"Lyric {ev.value!r} at tick {ev.position} is outside any phrase; it will not be displayed.")
            else:
                lyric = LyricEvent(ev.position, timing.tick_to_seconds(ev.position), ev.value,
                                   current.phrase_id, len(result.lyrics))
                current.lyrics.append(lyric)
                result.lyrics.append(lyric)

    if current is not None:
        close(current, None, explicit=False)                        # phrase terakhir tanpa akhir

    return result
