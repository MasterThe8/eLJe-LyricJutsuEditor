"""Structured, source-preserving model for lyric events inside a Jutsu block.

The model deliberately treats the original script as the source of truth.  It
projects only ``lyric`` event values for editing and applies updates to those
values without re-serializing any other event line.

This module is GUI-independent.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping


# Keep the complete prefix/suffix so updates can replace only the lyric value.
# The final quote is treated as the event string delimiter; quotes inside the
# value are retained as-is (the chart format's existing escaping is untouched).
_EVENT_LINE_RE = re.compile(
    r'^(?P<prefix>\s*\d+\s*=\s*E\s+")'
    r'(?P<name>\w+)'
    r'(?P<separator> ?)'
    r'(?P<value>.*)'
    r'(?P<suffix>"\s*)$'
)


class JutsuLyricsError(ValueError):
    """Base error for invalid Jutsu lyric model operations."""


class JutsuLyricsParseError(JutsuLyricsError):
    """Raised when a source line cannot safely be interpreted."""


class JutsuLyricsUpdateError(JutsuLyricsError):
    """Raised when an update targets a stale or non-lyric source line."""


@dataclass(frozen=True, slots=True)
class JutsuLyric:
    """One editable lyric event projected from the original Jutsu script.

    ``source_line`` is a zero-based index into ``JutsuLyricsDocument.source_lines``.
    It is the event identity; lyric text itself is never used as an ID.
    """

    source_line: int
    position: int
    raw_value: str


@dataclass(frozen=True, slots=True)
class _LyricLineParts:
    """Internal parsed pieces needed to preserve the exact original line."""

    position: int
    name: str
    prefix: str
    separator: str
    value: str
    suffix: str


def _split_line_ending(line: str) -> tuple[str, str]:
    """Return (content, line ending), preserving LF, CRLF, or CR."""
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith(("\n", "\r")):
        return line[:-1], line[-1:]
    return line, ""


def _parse_event_line(line: str) -> _LyricLineParts | None:
    """Parse the supported ``<position> = E \"<name> [value]\"`` shape.

    Returns None for non-event lines. A line that resembles an event but has
    malformed quoting is not modified; it is treated as a non-event line.
    """
    content, _ending = _split_line_ending(line)
    match = _EVENT_LINE_RE.match(content)
    if match is None:
        return None

    prefix = match.group("prefix")
    # Position is the first integer in the exact event prefix.
    position_match = re.match(r"\s*(\d+)", prefix)
    if position_match is None:  # defensive; guaranteed by _EVENT_LINE_RE
        return None

    return _LyricLineParts(
        position=int(position_match.group(1)),
        name=match.group("name"),
        prefix=prefix,
        separator=match.group("separator"),
        value=match.group("value"),
        suffix=match.group("suffix"),
    )


@dataclass(frozen=True, slots=True)
class JutsuLyricsDocument:
    """Immutable projection of lyric events from one Jutsu script.

    Attributes:
        source_lines: Original script lines, including their individual endings.
        lyrics:       Lyric events in source order; non-lyric events are omitted.

    Use :meth:`update_values` to produce an updated script. The original model
    remains unchanged, which makes it safe to retain as a baseline for Revert.
    """

    source_lines: tuple[str, ...]
    lyrics: tuple[JutsuLyric, ...]

    @classmethod
    def from_script(cls, script: str) -> "JutsuLyricsDocument":
        """Build a lyric-only projection from a Jutsu script string.

        Blank lines, malformed lines, and all non-lyric events remain in
        ``source_lines`` but are not included in ``lyrics``.
        """
        source_lines = tuple(script.splitlines(keepends=True))
        # str.splitlines() returns [] for an empty string, which is correct.
        lyrics: list[JutsuLyric] = []

        for line_index, line in enumerate(source_lines):
            parts = _parse_event_line(line)
            if parts is None or parts.name != "lyric":
                continue
            lyrics.append(
                JutsuLyric(
                    source_line=line_index,
                    position=parts.position,
                    raw_value=parts.value if parts.separator else "",
                )
            )

        return cls(source_lines=source_lines, lyrics=tuple(lyrics))

    @property
    def lyric_values(self) -> tuple[str, ...]:
        """Raw lyric values in source order."""
        return tuple(lyric.raw_value for lyric in self.lyrics)

    def update_values(self, updates: Mapping[int, str]) -> str:
        """Return the script with selected lyric values replaced.

        ``updates`` maps zero-based source-line indices to new raw lyric values.
        Only the value portion of a verified ``lyric`` event line is replaced.
        Position, event name, spacing before the value, closing quote, line
        ending, and every unrelated source line are preserved.

        Raises:
            TypeError: If an update value is not a string.
            JutsuLyricsUpdateError: If a line index is invalid, does not refer
                to a lyric event, or its position no longer matches the model.
        """
        if not updates:
            return "".join(self.source_lines)

        lyric_by_line = {lyric.source_line: lyric for lyric in self.lyrics}
        updated_lines = list(self.source_lines)

        for source_line, new_value in updates.items():
            if not isinstance(source_line, int) or isinstance(source_line, bool):
                raise JutsuLyricsUpdateError(
                    f"Invalid source line index: {source_line!r}."
                )
            if not isinstance(new_value, str):
                raise TypeError(
                    f"Lyric update for source line {source_line} must be str, "
                    f"not {type(new_value).__name__}."
                )

            lyric = lyric_by_line.get(source_line)
            if lyric is None:
                raise JutsuLyricsUpdateError(
                    f"Source line {source_line} is not a lyric event in this model."
                )
            if source_line < 0 or source_line >= len(updated_lines):
                raise JutsuLyricsUpdateError(
                    f"Source line {source_line} is outside the original script."
                )

            original_line = updated_lines[source_line]
            content, ending = _split_line_ending(original_line)
            parts = _parse_event_line(content)
            if (
                parts is None
                or parts.name != "lyric"
                or parts.position != lyric.position
                or (parts.value if parts.separator else "") != lyric.raw_value
            ):
                raise JutsuLyricsUpdateError(
                    f"Source line {source_line} no longer matches its original lyric event."
                )

            # Preserve whether the source used `lyric` or `lyric ` for an empty
            # value. When a non-empty value is inserted into an empty event,
            # ensure the required separator is present.
            separator = parts.separator
            if new_value and not separator:
                separator = " "
            updated_lines[source_line] = (
                parts.prefix
                + parts.name
                + separator
                + new_value
                + parts.suffix
                + ending
            )

        return "".join(updated_lines)


@dataclass(frozen=True, slots=True)
class LyricValueSpan:
    """Posisi nilai sebuah event ``lyric`` di dalam teks script (offset karakter, bukan nomor baris).

    ``start``/``end`` mengapit NILAI lirik saja (tanpa ``768 = E "lyric `` dan tanpa tanda kutip penutup), jadi
    teks di dalam rentang ini aman diedit. ``needs_separator``: event ditulis ``lyric`` tanpa spasi sehingga
    penyisipan harus menambahkan spasi pemisah lebih dulu.
    """

    source_line: int
    start: int
    end: int
    needs_separator: bool


def lyric_value_spans(script: str) -> tuple[LyricValueSpan, ...]:
    """Rentang nilai semua event ``lyric`` di ``script``, berurutan. Baris lain tidak disertakan."""
    spans: list[LyricValueSpan] = []
    offset = 0
    for line_index, line in enumerate(script.splitlines(keepends=True)):
        content, _ending = _split_line_ending(line)
        parts = _parse_event_line(content)
        if parts is not None and parts.name == "lyric":
            start = offset + len(parts.prefix) + len(parts.name) + len(parts.separator)
            value_length = len(parts.value) if parts.separator else 0
            spans.append(LyricValueSpan(line_index, start, start + value_length, not parts.separator))
        offset += len(line)
    return tuple(spans)


def extract_jutsu_lyrics(script: str) -> JutsuLyricsDocument:
    """Convenience function equivalent to ``JutsuLyricsDocument.from_script``."""
    return JutsuLyricsDocument.from_script(script)


def update_lyric_values(
    document: JutsuLyricsDocument,
    updates: Mapping[int, str],
) -> str:
    """Convenience wrapper for applying lyric updates to a parsed document."""
    return document.update_values(updates)
