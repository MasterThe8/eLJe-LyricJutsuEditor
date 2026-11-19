"""Logika event dan tag lirik."""

from core.lyrics.tags import TAG_SHORTCUTS  # noqa: F401
from core.lyrics.renderer import (  # noqa: F401
    convert_color_tags,
    convert_html_tags,
    convert_symbols,
    render_lyrics_html,
)
from core.lyrics.parser import (  # noqa: F401
    LyricPhrase,
    LyricStats,
    group_into_phrases,
    compute_stats,
    strip_tags,
)

from core.lyrics.jutsu_model import (  # noqa: F401
    JutsuLyric,
    JutsuLyricsDocument,
    JutsuLyricsError,
    JutsuLyricsParseError,
    JutsuLyricsUpdateError,
    extract_jutsu_lyrics,
    update_lyric_values,
)
from core.lyrics.renderer import (  # noqa: F401
    jutsu_tags_to_richtext,
    restore_symbols_from_display,
    richtext_to_jutsu_tags,
    custom_tags_to_richtext_html,
    richtext_html_to_custom_tags,
)
