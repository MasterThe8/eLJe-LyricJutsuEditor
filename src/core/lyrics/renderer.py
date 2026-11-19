"""Render and convert eLJe lyric markup without depending on a GUI toolkit.

The legacy gameplay renderer remains available through :func:`render_lyrics_html`.
The Jutsu editor uses the value-level conversion functions added below. These
functions only perform symbol conversion when explicitly requested: ``-``, ``_``
and ``=`` are source data and must remain editable/reversible by default.
"""
from __future__ import annotations

import html
import re
from difflib import SequenceMatcher
from html.parser import HTMLParser

from core.chart.events import events_to_lyric_lines
from core.lyrics.layout_tags import LAYOUT_TAGS, decode_layout_state, encode_layout_state, normalize_length_arg


# ---------------------------------------------------------------------------
# Existing gameplay/display renderer
# ---------------------------------------------------------------------------

_TAG_PATTERN = re.compile(r"<(\/?)(b|i|lowercase|uppercase)>")
_TAG_SPLIT = re.compile(r"(<[^>]*>)")


def convert_color_tags(text: str) -> str:
    """Convert legacy ``<color=#RRGGBB>`` markup to HTML spans."""
    result = text
    while True:
        start_idx = result.find("<color=")
        if start_idx == -1:
            return result
        end_tag_open = result.find(">", start_idx)
        text_end = result.find("</color>", end_tag_open + 1) if end_tag_open != -1 else -1
        if end_tag_open == -1 or text_end == -1:
            return result
        color_value = result[start_idx + len("<color="):end_tag_open]
        if not re.fullmatch(r"#[0-9a-fA-F]{3,8}", color_value):
            return result
        inner = result[end_tag_open + 1:text_end]
        span = f'<span style="color: {color_value};">{inner}</span>'
        result = result[:start_idx] + span + result[text_end + len("</color>"):]


def convert_html_tags(text: str) -> str:
    """Convert the legacy b/i/case tags to HTML spans."""
    styles = {
        "b": "font-weight: bold;",
        "i": "font-style: italic;",
        "lowercase": "text-transform: lowercase;",
        "uppercase": "text-transform: uppercase;",
    }
    parts: list[str] = []
    last_end = 0
    for match in _TAG_PATTERN.finditer(text):
        parts.append(text[last_end:match.start()])
        closing, name = match.groups()
        parts.append("</span>" if closing else f'<span style="{styles[name]}">')
        last_end = match.end()
    parts.append(text[last_end:])
    return "".join(parts)


_INVISIBLE_SYMBOL = "\u200B"
_SYMBOL_TABLE = str.maketrans({"-": _INVISIBLE_SYMBOL, "_": _INVISIBLE_SYMBOL, "=": "-"})
# Di game, "_" TIDAK benar-benar hilang: ia tampil sebagai spasi kosong. Tabel ini dipakai oleh
# tampilan yang meniru game (judul Jutsu, Live Lyrics Preview). Editor RichText tetap memakai
# _SYMBOL_TABLE / ``invisible_style`` supaya "_" masih bisa dilihat dan diedit.
_SYMBOL_TABLE_UNDERSCORE_SPACE = str.maketrans({"-": _INVISIBLE_SYMBOL, "_": " ", "=": "-"})


def _convert_visible_symbols(text: str, style: str) -> str:
    """Apply the same mapping but keep ``-``/``_`` visible inside a styled span.

    The Jutsu editor uses this so the symbols that are invisible during gameplay
    can still be seen (at low opacity) while editing.
    """
    output: list[str] = []
    for char in text:
        if char in "-_":
            output.append(f'<span style="{style}">{char}</span>')
        elif char == "=":
            output.append("-")
        else:
            output.append(char)
    return "".join(output)


def convert_symbols(
    text: str,
    *,
    invisible_style: str | None = None,
    underscore_as_space: bool = False,
) -> str:
    """Convert gameplay-only lyric symbols.

    By default ``-`` and ``_`` become a zero-width space (invisible in the game)
    and ``=`` becomes ``-``. Pass ``invisible_style`` to keep the invisible
    symbols visible inside a span with that CSS style; this is used by the Jutsu
    editor to render them at 20% opacity instead of hiding them completely.

    In the game ``_`` is not removed but shown as an empty space. Pass
    ``underscore_as_space=True`` to mimic that: ``_`` becomes `` `` (a regular
    space) while ``-`` stays a zero-width space and ``=`` still becomes ``-``.
    It is ignored when ``invisible_style`` is given (the editor keeps ``_``
    visible so it can still be edited).

    Only text outside tags is converted. Tags such as ``<color=#RRGGBB>`` must
    keep their ``=`` attribute intact.
    """
    table = _SYMBOL_TABLE_UNDERSCORE_SPACE if underscore_as_space else _SYMBOL_TABLE
    parts = _TAG_SPLIT.split(text)
    for index in range(0, len(parts), 2):
        segment = parts[index]
        parts[index] = (
            segment.translate(table)
            if invisible_style is None
            else _convert_visible_symbols(segment, invisible_style)
        )
    return "".join(parts)


def restore_symbols_from_display(display_baseline: str, raw_baseline: str, edited: str) -> str:
    """Map characters unchanged from a converted display back to their raw form.

    :func:`convert_symbols` renders ``=`` as ``-``. When the rich-text editor is
    synchronized back to the raw lyric value, unchanged parts must use the
    original characters so simply opening a Jutsu does not rewrite ``=``.
    """
    if edited == display_baseline:
        return raw_baseline
    if display_baseline == raw_baseline or len(display_baseline) != len(raw_baseline):
        return edited

    output: list[str] = []
    matcher = SequenceMatcher(None, display_baseline, edited, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        output.append(raw_baseline[i1:i2] if tag == "equal" else edited[j1:j2])
    return "".join(output)


def render_lyrics_html(
    events_text: str,
    *,
    apply_symbol_conversion: bool = False,
    underscore_as_space: bool = False,
) -> str:
    """Render a complete chart Events body for the existing display preview.

    ``underscore_as_space`` is forwarded to :func:`convert_symbols` and only has
    an effect together with ``apply_symbol_conversion``.
    """
    lyric_lines = events_to_lyric_lines(events_text)
    if not lyric_lines:
        return ""
    if apply_symbol_conversion:
        lyric_lines = [
            convert_symbols(line, underscore_as_space=underscore_as_space)
            for line in lyric_lines
        ]
    joined = "<br>".join(lyric_lines)
    return convert_color_tags(convert_html_tags(joined))


# ---------------------------------------------------------------------------
# Jutsu lyric value <-> rich-text HTML conversion
# ---------------------------------------------------------------------------

# Tag format biasa punya padanan stabil di HTML QTextDocument (span + style).
_SIMPLE_TAG_STYLES = {
    "b": "font-weight: bold;",
    "i": "font-style: italic;",
    "lowercase": "text-transform: lowercase;",
    "uppercase": "text-transform: uppercase;",
    "smallcaps": "font-variant: small-caps;",
    "sub": "vertical-align: sub;",
    "sup": "vertical-align: super;",
}
# Tag tata letak game (voffset/mspace/cspace) TIDAK punya padanan CSS yang selamat dari ``QTextEdit.toHtml()``
# (Qt membuang baseline offset dan letter spacing). Nilai mentahnya dibawa di atribut ``title`` span, yang dipetakan Qt
# ke tooltip format karakter dan ikut round-trip. Efek visualnya (baseline offset / letter spacing) dipasang oleh
# ``ui.widgets.game_richtext`` dengan rumus yang sama dengan Live Lyrics Preview; lihat ``core.lyrics.layout_tags``.
_LAYOUT_NAMES = "|".join(LAYOUT_TAGS)
_CUSTOM_TAG_RE = re.compile(
    rf"</?(?:b|i|lowercase|uppercase|smallcaps|sub|sup|color|{_LAYOUT_NAMES})>"
    r"|<color=#[0-9a-fA-F]{3,8}>"
    rf"|<(?:{_LAYOUT_NAMES})\s*=\s*[^<>]*?\s*>"
    r"|<br\s*/?>",
    re.IGNORECASE,
)


def _classify_tag(token: str) -> tuple[str, str, str | None]:
    """Token tag → ``(jenis, nama, argumen)``.

    ``jenis``: ``br`` | ``open`` | ``close`` | ``literal``. ``literal`` = pembuka yang tidak punya argumen valid
    (``<color>``, ``<voffset=abc>``): tidak diinterpretasi dan ditampilkan apa adanya, seperti sebelumnya.
    """
    if token[:3].lower() == "<br":
        return "br", "br", None
    if token.startswith("</"):
        return "close", token[2:-1].strip().lower(), None
    name, has_arg, arg = token[1:-1].partition("=")
    name = name.strip().lower()
    if not has_arg:
        # <b>, <i>, ... memang tanpa argumen; <color> dan tag tata letak tanpa argumen tidak berarti apa-apa.
        return ("literal" if name == "color" or name in LAYOUT_TAGS else "open"), name, None
    arg = arg.strip()
    if name in LAYOUT_TAGS:
        valid = normalize_length_arg(arg)
        return ("open", name, valid) if valid is not None else ("literal", name, None)
    return "open", name, arg                       # color: regex sudah menjamin heksadesimal valid


def _nesting_is_valid(tokens) -> bool:
    stack: list[str] = []
    for _match, kind, name, _arg in tokens:
        if kind == "br":
            continue
        if kind == "close":
            if not stack or stack[-1] != name:
                return False
            stack.pop()
        else:
            stack.append(name)
    return not stack


def tags_are_balanced(value: str) -> bool:
    """``True`` bila semua tag di ``value`` bersarang dan tertutup dengan benar.

    Nilai yang tidak seimbang tampil sebagai teks literal di RichText editor (lihat
    :func:`jutsu_tags_to_richtext`), jadi penyisipan tag di PlainText memakai ini untuk menolak sisipan yang
    memotong tag lain.
    """
    return _nesting_is_valid([(m, *_classify_tag(m.group(0))) for m in _CUSTOM_TAG_RE.finditer(value)])


def jutsu_tags_to_richtext(
    value: str,
    *,
    apply_symbol_conversion: bool = False,
    invisible_style: str | None = None,
) -> str:
    """Convert one raw Jutsu lyric value to safe HTML for ``QTextEdit.setHtml``.

    Only known eLJe tags are interpreted. All ordinary text is HTML-escaped.
    Unknown tags, and known tags with an invalid argument, remain visible as
    literal text rather than being silently stripped.

    ``voffset``/``mspace``/``cspace`` become ``<span title="...">`` carrying the
    raw tag values; the editor turns that into real baseline/spacing formatting
    (see ``ui.widgets.game_richtext``) using the Live Lyrics Preview rules.

    Args:
        value: Raw lyric value from the Jutsu script.
        apply_symbol_conversion:
            Apply :func:`convert_symbols` to the rendered HTML. The Jutsu
            editor enables this so lyrics look like they do during gameplay.
        invisible_style:
            CSS style used for ``-``/``_`` when symbol conversion is enabled.
            The Jutsu editor passes a 20%-opacity color so those symbols remain
            visible while editing instead of disappearing completely.

    Returns:
        HTML ready for ``QTextEdit.setHtml``.
    """
    if not isinstance(value, str):
        raise TypeError("lyric value must be str")

    def finish(rendered: str) -> str:
        if not apply_symbol_conversion:
            return rendered
        return convert_symbols(rendered, invisible_style=invisible_style)

    tokens = [(m, *_classify_tag(m.group(0))) for m in _CUSTOM_TAG_RE.finditer(value)]

    # Validate nesting first. Rendering a malformed tag sequence by silently
    # auto-closing it would change the user's raw lyric value on the next sync.
    if not _nesting_is_valid(tokens):
        return finish(html.escape(value, quote=False))

    output: list[str] = []
    stack: list[tuple[str, str | None]] = []
    cursor = 0

    for match, kind, name, arg in tokens:
        output.append(html.escape(value[cursor:match.start()], quote=False))
        token = match.group(0)
        cursor = match.end()

        if kind == "br":
            output.append("<br>")
        elif kind == "literal":
            output.append(html.escape(token, quote=False))
        elif kind == "close":
            # Close only a matching most-recent tag. Malformed/unbalanced
            # closers are preserved as text to avoid inventing structure.
            if stack and stack[-1][0] == name:
                stack.pop()
                output.append("</span>")
            else:
                output.append(html.escape(token, quote=False))
        elif name == "color":
            output.append(f'<span style="color: {arg};">')
            stack.append((name, arg))
        elif name in LAYOUT_TAGS:
            stack.append((name, arg))
            # Tiap span membawa state EFEKTIF (yang terdalam menang): tooltip hanya satu properti per karakter,
            # jadi span bersarang tidak boleh saling menimpa.
            state = {n: a for n, a in stack if n in LAYOUT_TAGS and a is not None}
            output.append(f'<span title="{html.escape(encode_layout_state(state), quote=True)}">')
        else:
            output.append(f'<span style="{_SIMPLE_TAG_STYLES[name]}">')
            stack.append((name, arg))

    output.append(html.escape(value[cursor:], quote=False))
    output.extend("</span>" for _ in reversed(stack))
    return finish("".join(output))


_MERGE_TOKEN_RE = re.compile(
    rf"<(/?)(b|i|lowercase|uppercase|smallcaps|sub|sup|color|{_LAYOUT_NAMES})(?:=([^<>]*))?>"
)


def _merge_adjacent_tags(value: str) -> str:
    """Gabungkan tag format identik yang bersebelahan (mis. ``</b><b>``, ``</voffset><voffset=1>``).

    Rich text menyimpan satu run per perubahan format. Simbol ``-``/``_`` yang ditampilkan samar oleh editor dan
    letter spacing per karakter milik ``mspace`` memecah run, sehingga tanpa penggabungan ini satu kata bisa
    menghasilkan banyak tag yang tidak perlu. Tag ber-argumen (``color``, ``voffset``, ``mspace``, ``cspace``) hanya
    digabung bila argumen tag yang baru ditutup sama persis dengan yang baru dibuka; karena itu pemindaian
    memakai stack yang mengingat argumen tiap pembuka. Struktur yang tidak seimbang dibiarkan apa adanya.
    """
    while True:
        stack: list[tuple[str, str | None]] = []
        last_close: tuple[str, str | None, int, int] | None = None
        cut: tuple[int, int] | None = None
        for match in _MERGE_TOKEN_RE.finditer(value):
            closing, name, arg = match.group(1) == "/", match.group(2), match.group(3)
            if closing:
                if arg is not None or not stack or stack[-1][0] != name:
                    return value                       # tidak seimbang (mis. teks literal): jangan menebak
                opened_name, opened_arg = stack.pop()
                last_close = (opened_name, opened_arg, match.start(), match.end())
                continue
            if (last_close is not None and last_close[3] == match.start()
                    and last_close[0] == name and last_close[1] == arg):
                cut = (last_close[2], match.end())
                break
            stack.append((name, arg))
            last_close = None
        if cut is None:
            return value
        value = value[:cut[0]] + value[cut[1]:]


# Urutan kanonik untuk tag yang "umur"-nya sama: tag tata letak di luar, lalu format huruf, lalu warna.
_FORMAT_ORDER = (*LAYOUT_TAGS, "b", "i", "lowercase", "uppercase", "smallcaps", "sub", "sup", "color")
_HOIST_TOKEN_RE = re.compile(
    rf"<(/?)(b|i|lowercase|uppercase|smallcaps|sub|sup|color|{_LAYOUT_NAMES})(?:=([^<>]*))?>|(<br>)"
)


def _hoist_tags(value: str) -> str:
    """Susun ulang nesting tag agar jumlah tag minimal.

    Qt menyimpan teks sebagai fragmen datar (tiap fragmen membawa SEMUA format-nya), jadi urutan nesting hasil
    ekstraksi harus dipilih. Tag yang berlaku paling lama ditaruh paling luar; dengan begitu tag yang lebih
    pendek tidak memaksa tag yang lebih panjang ditutup dan dibuka lagi. Contoh::

        <color=#0F0>w</color><mspace=0.6em><color=#0F0>orl</color></mspace><color=#0F0>d</color>
        → <color=#0F0>w<mspace=0.6em>orl</mspace>d</color>

    Maknanya tidak berubah (tiap karakter tetap membawa himpunan tag yang sama). Struktur yang tidak seimbang atau
    memuat tag bernama sama yang bersarang dibiarkan apa adanya.
    """
    chunks: list[tuple[str, tuple[tuple[str, str | None], ...]]] = []     # (teks atau "<br>", tag yang berlaku)
    stack: list[tuple[str, str | None]] = []
    position = 0
    for match in _HOIST_TOKEN_RE.finditer(value):
        if match.start() > position:
            chunks.append((value[position:match.start()], tuple(stack)))
        position = match.end()
        if match.group(4):
            chunks.append(("<br>", tuple(stack)))
            continue
        closing, name, arg = match.group(1) == "/", match.group(2), match.group(3)
        if closing:
            if arg is not None or not stack or stack[-1][0] != name:
                return value
            stack.pop()
        else:
            if any(open_name == name for open_name, _ in stack):
                return value
            stack.append((name, arg))
    if stack:
        return value
    if position < len(value):
        chunks.append((value[position:], ()))
    if not chunks:
        return value

    runs: list[dict[tuple[str, str | None], int]] = [{} for _ in chunks]     # berapa chunk berturut-turut tag ini berlaku
    for index in range(len(chunks) - 1, -1, -1):
        for tag in chunks[index][1]:
            following = runs[index + 1].get(tag, 0) if index + 1 < len(chunks) else 0
            runs[index][tag] = 1 + following

    output: list[str] = []
    opened: list[tuple[str, str | None]] = []
    for index, (text, tags) in enumerate(chunks):
        wanted = set(tags)
        cut = next((i for i, tag in enumerate(opened) if tag not in wanted), None)
        if cut is not None:                                    # tutup dari yang terdalam sampai tag yang sudah tak berlaku
            output.extend(f"</{name}>" for name, _arg in reversed(opened[cut:]))
            del opened[cut:]
        missing = sorted((tag for tag in tags if tag not in opened),
                         key=lambda tag: (-runs[index][tag], _FORMAT_ORDER.index(tag[0])))
        for name, arg in missing:
            output.append(f"<{name}>" if arg is None else f"<{name}={arg}>")
            opened.append((name, arg))
        output.append(text)
    output.extend(f"</{name}>" for name, _arg in reversed(opened))
    return "".join(output)


class _RichTextToJutsuParser(HTMLParser):
    """Extract supported character formatting from QTextDocument HTML."""

    _IGNORED = {"html", "head", "body", "meta", "title", "style", "script"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.stack: list[tuple[str, list[str]]] = []
        self._skip_depth = 0
        self._last_was_break = False
        self._last_break_explicit = False

    def _append_break(self, *, explicit: bool = False) -> None:
        if self.parts and (explicit or not self._last_was_break):
            self.parts.append("<br>")
            self._last_was_break = True
            self._last_break_explicit = explicit

    @staticmethod
    def _style_tags(style: str) -> list[str]:
        declarations: dict[str, str] = {}
        for declaration in style.split(";"):
            if ":" not in declaration:
                continue
            key, value = declaration.split(":", 1)
            declarations[key.strip().lower()] = value.strip()

        tags: list[str] = []
        weight = declarations.get("font-weight", "").lower()
        if weight in {"bold", "bolder"}:
            tags.append("b")
        else:
            try:
                if int(weight) >= 600:
                    tags.append("b")
            except ValueError:
                pass

        if declarations.get("font-style", "").lower() in {"italic", "oblique"}:
            tags.append("i")

        transform = declarations.get("text-transform", "").lower()
        if transform in {"lowercase", "uppercase"}:
            tags.append(transform)

        if declarations.get("font-variant", "").lower() == "small-caps":
            tags.append("smallcaps")

        vertical = declarations.get("vertical-align", "").lower()
        if vertical in {"sub", "super"}:
            tags.append("sub" if vertical == "sub" else "sup")

        color = declarations.get("color", "")
        if re.fullmatch(r"#[0-9a-fA-F]{3,8}", color):
            tags.append(f"color={color.upper()}")
        return tags

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._IGNORED:
            if tag in {"style", "script"}:
                self._skip_depth += 1
            return
        if self._skip_depth:
            return

        attr_map = dict(attrs)
        opened: list[str] = []
        if tag in {"b", "strong"}:
            opened.append("b")
        elif tag in {"i", "em"}:
            opened.append("i")
        elif tag == "sub":
            opened.append("sub")
        elif tag == "sup":
            opened.append("sup")
        elif tag == "span":
            # Tag tata letak (dari ``title``) paling luar: state-nya paling stabil antar run, sehingga
            # ``_merge_adjacent_tags`` bisa menyatukan run yang hanya berbeda b/i/color.
            layout = decode_layout_state(attr_map.get("title"))
            opened.extend(f"{name}={layout[name]}" for name in LAYOUT_TAGS if name in layout)
            opened.extend(self._style_tags(attr_map.get("style") or ""))

        for name in opened:
            self.parts.append(f"<{name}>")
        if tag != "br":
            self.stack.append((tag, opened))

        if tag in {"p", "div"}:
            # QTextDocument commonly wraps each visual paragraph in <p>.
            # The first paragraph does not need a leading break.
            if self.parts and self.parts[-1] != "<br>":
                self._append_break()
        elif tag == "br":
            self._append_break(explicit=True)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "br":
            self._append_break(explicit=True)
        else:
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"style", "script"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag in self._IGNORED or self._skip_depth:
            return

        if tag in {"p", "div"}:
            self._append_break()

        # Match the corresponding opening element rather than blindly popping
        # the most recent frame (unknown HTML elements may be present).
        for index in range(len(self.stack) - 1, -1, -1):
            open_tag, opened = self.stack[index]
            if open_tag == tag:
                del self.stack[index]
                for name in reversed(opened):
                    self.parts.append(f"</{name.partition('=')[0]}>")
                break

    def handle_data(self, data: str) -> None:
        if self._skip_depth or not data:
            return
        # Pretty-printed HTML often contains indentation between block tags;
        # it is document formatting, not lyric whitespace. Preserve whitespace
        # inside paragraphs and inline elements.
        inside_block = any(tag in {"p", "div"} for tag, _opened in self.stack)
        if data.isspace() and not inside_block:
            return
        self.parts.append(data)
        self._last_was_break = False
        self._last_break_explicit = False

    def get_value(self) -> str:
        result = "".join(self.parts)
        # QTextDocument's final paragraph terminator is not lyric content, but
        # an explicit <br> at the end of the value is.
        if result.endswith("<br>") and not self._last_break_explicit:
            result = result[:-4]
        return _hoist_tags(_merge_adjacent_tags(result))


def richtext_to_jutsu_tags(richtext_html: str) -> str:
    """Convert ``QTextEdit.toHtml()`` output to eLJe custom lyric tags.

    Qt document wrappers and unsupported visual CSS are discarded. Supported
    formatting is normalized to eLJe tags; ``voffset``/``mspace``/``cspace`` are
    read back from the ``title`` attribute that ``jutsu_tags_to_richtext`` wrote. This function accepts HTML text,
    not a QTextEdit instance, keeping the core renderer GUI-independent.
    """
    if not isinstance(richtext_html, str):
        raise TypeError("richtext_html must be str")
    parser = _RichTextToJutsuParser()
    parser.feed(richtext_html)
    parser.close()
    return parser.get_value()


# Backwards-friendly aliases with explicit direction in their names.
custom_tags_to_richtext_html = jutsu_tags_to_richtext
richtext_html_to_custom_tags = richtext_to_jutsu_tags
