"""PreviewSession — semua data turunan satu chart untuk Live Lyrics Preview.

Murni Python (tanpa GUI). Merangkai urutan spesifikasi 12.3: baca metadata → resolve audio →
TimingEngine → parser lirik → scheduler. Sesi bersifat *immutable*: setiap perubahan chart/teks
menghasilkan sesi baru, sehingga data chart lama tidak mungkin "bocor" ke preview chart baru.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Collection

from core.preview.audio_resolver import AudioResolution, AudioStatus, resolve_chart_audio
from core.preview.chart_info import ChartInfo, read_chart_info_from_sections
from core.preview.lyrics_parser import ParsedLyrics, parse_lyrics
from core.preview.scheduler import LyricScheduler
from core.preview.timing_engine import TimingEngine
from core.preview.transition import TransitionTimeline


@dataclass(frozen=True)
class PreviewSession:
    chart_path: str | None
    info: ChartInfo
    timing: TimingEngine
    parsed: ParsedLyrics
    scheduler: LyricScheduler
    timeline: TransitionTimeline
    audio: AudioResolution
    warnings: tuple[str, ...]            # catatan teknis (untuk log/tooltip)

    @property
    def has_lyrics(self) -> bool:
        return len(self.scheduler) > 0

    @property
    def title(self) -> str:
        if self.info.song.name:
            return self.info.song.name
        return Path(self.chart_path).name if self.chart_path else ""

    @property
    def notices(self) -> tuple[str, ...]:
        """Pesan singkat untuk pengguna, urut prioritas (kosong = semuanya siap)."""
        out: list[str] = []
        if self.audio.status is not AudioStatus.OK:
            out.append(self.audio.message)
        if not self.has_lyrics:
            out.append("This chart has no lyrics to display.")
        return tuple(out)


def build_preview_session(
    song_section: str,
    sync_section: str,
    events_text: str,
    chart_path: str | Path | None,
    *,
    supported_extensions: Collection[str] | None = None,
) -> PreviewSession:
    """Bangun sesi dari teks section chart.

    Args:
        song_section / sync_section: ``ChartDocument.song`` / ``.sync_track``.
        events_text: teks body ``[Events]`` TERKINI (isi editor — bisa berbeda dari file di disk).
        chart_path:  lokasi file chart aktif (untuk mencari audio).
    """
    info = read_chart_info_from_sections(song_section or "", sync_section or "")
    timing = TimingEngine.from_chart_info(info)
    parsed = parse_lyrics(events_text or "", timing)
    audio = resolve_chart_audio(chart_path, info.song.music_stream,
                                supported_extensions=supported_extensions)
    scheduler = LyricScheduler(parsed, timing)
    return PreviewSession(
        chart_path=None if chart_path is None else str(chart_path),
        info=info,
        timing=timing,
        parsed=parsed,
        scheduler=scheduler,
        timeline=TransitionTimeline(scheduler),
        audio=audio,
        warnings=tuple(info.warnings) + tuple(timing.warnings) + tuple(parsed.warnings),
    )


def build_preview_session_from_document(doc, events_text: str | None = None, *,
                                        supported_extensions: Collection[str] | None = None) -> PreviewSession:
    """Pintasan untuk ``ChartDocument``. *events_text* default ke ``doc.events_body``."""
    return build_preview_session(
        getattr(doc, "song", "") or "",
        getattr(doc, "sync_track", "") or "",
        doc.events_body if events_text is None else events_text,
        getattr(doc, "file_path", None),
        supported_extensions=supported_extensions,
    )
