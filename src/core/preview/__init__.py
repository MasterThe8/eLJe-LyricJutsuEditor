"""Logika murni (tanpa GUI) untuk Live Lyrics Preview: audio resolver, timing, dan parser lirik."""

from core.preview.audio_resolver import (  # noqa: F401
    AudioResolution,
    AudioStatus,
    resolve_audio_for_chart,
    resolve_chart_audio,
)
from core.preview.chart_info import (  # noqa: F401
    ChartInfo,
    ChartSongInfo,
    parse_song_section,
    parse_sync_track,
    read_chart_info,
    read_chart_info_from_sections,
)
from core.preview.lyrics_parser import (  # noqa: F401
    LyricEvent,
    ParsedLyrics,
    PreviewPhrase,
    parse_lyrics,
)
from core.preview.timing_engine import TempoEvent, TimingEngine  # noqa: F401
from core.preview.scheduler import LyricScheduler, LyricState, SchedulePhase  # noqa: F401
from core.preview.controller import (  # noqa: F401
    DEFAULT_SPEED,
    SPEED_OPTIONS,
    AudioBackend,
    NullAudioBackend,
    PlaybackState,
    PreviewController,
    format_speed,
    format_time,
)
from core.preview.session import (  # noqa: F401
    PreviewSession,
    build_preview_session,
    build_preview_session_from_document,
)
from core.preview.phrase_display import (  # noqa: F401
    PhraseDisplay,
    Run,
    build_phrase_display,
    get_phrase_display,
    parse_color,
)
from core.preview.phrase_layout import PhraseLayout, layout_phrase  # noqa: F401
from core.preview.transition import Kind, Role, Scene, SceneItem, SceneStyle, TransitionTimeline  # noqa: F401
