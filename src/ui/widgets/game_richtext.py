"""Eksekusi tag ``voffset`` / ``mspace`` / ``cspace`` di ``QTextEdit`` (RichText editor Jutsu Editor).

Live Lyrics Preview menggambar teks sendiri per karakter (``ui.widgets.game_text.draw_text``). ``QTextEdit`` tidak
bisa digambar seperti itu karena harus tetap bisa diedit, jadi efek yang sama dibuat dari format karakter Qt:

==========  ===========================================  ==============================================
Tag         Preview (``draw_text``)                      RichText editor (modul ini)
==========  ===========================================  ==============================================
voffset     ``y = baseline - voffset * size_px``         ``QTextCharFormat.setBaselineOffset`` (% tinggi font)
cspace      ``x += advance + cspace * size_px``          letter spacing ABSOLUT (px) per karakter
mspace      sel ``mspace * size_px``, tinta ditengahkan  letter spacing absolut per karakter, dihitung oleh
                                                         ``core.lyrics.layout_tags.plan_block_spacing`` + indent baris
==========  ===========================================  ==============================================

Pembagian tugas
---------------
* **Sumber kebenaran = tooltip format karakter** (``decode_layout_state``). Hanya tooltip yang selamat dari
  ``toHtml()`` (sebagai ``<span title>``); baseline offset dan letter spacing dibuang Qt. Karena itu round-trip
  RichText → tag Jutsu selalu membaca tooltip, tidak pernah membaca efek visualnya.
* **Efek visual = turunan.** :func:`reflow_layout` menghitung ulang baseline offset / letter spacing / indent dari tooltip
  tiap kali isi atau font berubah. Fungsi ini idempoten dan hanya menulis bila ada selisih, serta menggabungkan
  perubahannya ke langkah undo yang sedang berjalan (``joinPreviousEditBlock``) sehingga Ctrl+Z tidak memecah
  satu aksi menjadi dua.

Catatan: simbol ``-`` / ``_`` ditampilkan samar oleh editor sehingga ikut menempati sel ``mspace`` (di preview
keduanya tak tampak / jadi spasi). Itu murni dekorasi editor; nilai tag yang tersimpan tidak terpengaruh.
"""
from __future__ import annotations

import base64
import html as html_module
import json
import math
import re
from dataclasses import dataclass

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import (
    QFont,
    QFontInfo,
    QRegularExpressionValidator,
    QTextBlock,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextDocumentFragment,
    QTextFormat,
)
from PySide6.QtWidgets import QDialog, QInputDialog, QLineEdit, QTextEdit, QWidget

from core.lyrics.layout_tags import (
    LAYOUT_TAGS,
    LENGTH_PATTERN,
    CharLayout,
    decode_layout_state,
    encode_layout_state,
    layout_from_state,
    normalize_length_arg,
    plan_block_spacing,
)
from ui.widgets.game_text import RunFonts

_LINE_SEPARATOR = "\u2028"          # <br> di dalam satu event (lihat ``JutsuItemWidget._insert_rich_tag``)
_EPSILON = 1e-3

# (judul dialog, petunjuk) per tag.
LAYOUT_TAG_HELP: dict[str, tuple[str, str]] = {
    "voffset": ("Vertical offset (VOffset)",
                "Shifts the text baseline. Positive moves the text up.\nExamples: 0.3em   -10   25%"),
    "mspace": ("Monospace (MSpace)",
               "Gives every character a fixed-width cell with the glyph centered in it.\nExamples: 0.6em   20   50%"),
    "cspace": ("Character spacing (CSpace)",
               "Adds extra space after every character.\nExamples: 0.1em   5   10%"),
}


# ─────────────────────────────────────────────────────────────────────────────
#  State tag  <->  format karakter
# ─────────────────────────────────────────────────────────────────────────────
def layout_state(fmt: QTextCharFormat) -> dict[str, str]:
    """Nilai mentah tag tata letak yang melekat pada ``fmt`` (``{}`` bila tidak ada)."""
    return decode_layout_state(fmt.toolTip())


def layout_arg_at(cursor: QTextCursor, tag: str) -> str | None:
    """Nilai ``tag`` pada seleksi (karakter pertama) atau pada posisi kursor; dipakai mengisi awal dialog."""
    if cursor.hasSelection():
        document = cursor.document()
        probe = QTextCursor(document)
        probe.setPosition(cursor.selectionStart() + 1)       # format karakter DI DEPAN posisi ini = karakter pertama seleksi
        return layout_state(probe.charFormat()).get(tag)
    return layout_state(cursor.charFormat()).get(tag)


def apply_layout_tag(cursor: QTextCursor, tag: str, arg: str) -> None:
    """Pasang ``<tag=arg>`` pada seleksi, atau pada format ketikan berikutnya bila tidak ada seleksi.

    Tag lain yang sudah ada pada karakter itu dipertahankan; tag yang sama diganti (yang terdalam menang, seperti
    di preview). Hanya state (tooltip) yang ditulis; efek visualnya dipasang oleh :func:`reflow_layout` begitu
    dokumen berubah.
    """
    if tag not in LAYOUT_TAGS:
        raise ValueError(f"not a layout tag: {tag!r}")
    value = normalize_length_arg(arg)
    if value is None:
        raise ValueError(f"invalid {tag} value: {arg!r}")

    if not cursor.hasSelection():
        state = layout_state(cursor.charFormat())
        state[tag] = value
        fmt = QTextCharFormat()
        fmt.setToolTip(encode_layout_state(state))
        cursor.mergeCharFormat(fmt)
        return

    document = cursor.document()
    start, end = cursor.selectionStart(), cursor.selectionEnd()
    changes: list[tuple[int, int, str]] = []
    block = document.findBlock(start)
    while block.isValid() and block.position() < end:        # kumpulkan dulu: mengubah format membatalkan iterator
        it = block.begin()
        while not it.atEnd():
            fragment = it.fragment()
            first = max(fragment.position(), start)
            last = min(fragment.position() + fragment.length(), end)
            if first < last:
                state = layout_state(fragment.charFormat())
                state[tag] = value
                changes.append((first, last, encode_layout_state(state)))
            it += 1
        block = block.next()

    editor = QTextCursor(document)
    for first, last, title in changes:
        editor.setPosition(first)
        editor.setPosition(last, QTextCursor.MoveMode.KeepAnchor)
        fmt = QTextCharFormat()
        fmt.setToolTip(title)
        editor.mergeCharFormat(fmt)


# ─────────────────────────────────────────────────────────────────────────────
#  Ekspor HTML yang TIDAK bergantung pada versi Qt
# ─────────────────────────────────────────────────────────────────────────────
# ``toHtml()`` Qt baru (≈6.9+) menulis tooltip format karakter sebagai ``<span title>``, tetapi Qt lebih lama
# (mis. 6.8) TIDAK — padahal ``insertHtml`` membaca ``title`` di semua versi. Akibatnya, bila nilai tag dibaca dari
# ``toHtml()``, RichText tampak benar (impor jalan) tetapi tag tidak pernah sampai ke Jutsu Script. Karena itu state
# tag selalu diambil langsung dari format karakter dan disuntikkan ke HTML di sini.
_FRAGMENT_START = "<!--StartFragment-->"
_FRAGMENT_END = "<!--EndFragment-->"
_TITLE_ATTRIBUTE_RE = re.compile(r'\s+title="[^"]*"')
_SNAPSHOT_RE = re.compile(r"<!--elje-layout:([A-Za-z0-9+/=]*)-->\s*$")


def _fragment_inner_html(fragment_html: str) -> str | None:
    start, end = fragment_html.find(_FRAGMENT_START), fragment_html.rfind(_FRAGMENT_END)
    if start < 0 or end < start:
        return None
    return fragment_html[start + len(_FRAGMENT_START):end]


def block_html(block: QTextBlock) -> str | None:
    """HTML satu blok yang SELALU memuat state tag tata letak, atau ``None`` bila blok tidak punya tag tata letak
    (pemanggil lalu memakai ekspor bawaan Qt, yang untuk format biasa sama di semua versi).

    Tiap fragmen diekspor sendiri-sendiri oleh Qt (gaya b/i/warna/dll. tetap hasil Qt), lalu dibungkus
    ``<span title="…">`` berisi state yang dibaca dari format karakternya. ``title`` bawaan Qt (bila ada) dibuang
    dulu supaya tidak ganda di Qt yang mengekspornya.
    """
    document = block.document()
    pieces: list[str] = []
    found = False
    it = block.begin()
    while not it.atEnd():
        fragment = it.fragment()
        it += 1
        cursor = QTextCursor(document)
        cursor.setPosition(fragment.position())
        cursor.setPosition(fragment.position() + fragment.length(), QTextCursor.MoveMode.KeepAnchor)
        inner = _fragment_inner_html(QTextDocumentFragment(cursor).toHtml())
        if inner is None:
            return None
        state = layout_state(fragment.charFormat())
        if state:
            found = True
            title = html_module.escape(encode_layout_state(state), quote=True)
            inner = f'<span title="{title}">{_TITLE_ATTRIBUTE_RE.sub("", inner)}</span>'
        pieces.append(inner)
    return f"<html><body><p>{''.join(pieces)}</p></body></html>" if found else None


def layout_snapshot(document: QTextDocument) -> list[list]:
    """``[[awal, akhir, tooltip], …]`` untuk semua fragmen yang membawa state tag tata letak."""
    snapshot: list[list] = []
    block = document.begin()
    while block.isValid():
        it = block.begin()
        while not it.atEnd():
            fragment = it.fragment()
            it += 1
            state = layout_state(fragment.charFormat())
            if state:
                snapshot.append([fragment.position(), fragment.position() + fragment.length(),
                                 encode_layout_state(state)])
        block = block.next()
    return snapshot


def draft_html(edit: QTextEdit) -> str:
    """HTML RichText untuk disimpan sebagai draft: ``toHtml()`` + snapshot state tag (tidak bergantung versi Qt)."""
    snapshot = layout_snapshot(edit.document())
    html = edit.toHtml()
    if not snapshot:
        return html
    payload = base64.b64encode(json.dumps(snapshot).encode("utf-8")).decode("ascii")
    return f"{html}<!--elje-layout:{payload}-->"


def restore_draft_html(edit: QTextEdit, html: str) -> None:
    """Kebalikan :func:`draft_html`: ``setHtml`` lalu pasang kembali state tag dari snapshot."""
    snapshot: list[list] = []
    match = _SNAPSHOT_RE.search(html)
    if match:
        html = html[:match.start()]
        try:
            snapshot = json.loads(base64.b64decode(match.group(1)).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            snapshot = []
    edit.setHtml(html)
    document = edit.document()
    limit = document.characterCount() - 1
    cursor = QTextCursor(document)
    for start, end, title in snapshot:
        if 0 <= start < end <= limit and decode_layout_state(title):
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            fmt = QTextCharFormat()
            fmt.setToolTip(title)
            cursor.mergeCharFormat(fmt)


# ─────────────────────────────────────────────────────────────────────────────
#  Reflow: state → baseline offset / letter spacing / indent
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(slots=True)
class _Char:
    ch: str
    position: int
    fragment: int                # indeks fragmen dalam blok (pengelompokan op)
    base: QTextCharFormat        # format fragmen asal (salinan dipakai saat menulis)
    layout: CharLayout
    bold: bool
    italic: bool
    caps: QFont.Capitalization
    spacing: float               # letter spacing absolut yang SEKARANG terpasang (px)
    baseline: float              # baseline offset yang SEKARANG terpasang (%)


def _current_spacing(fmt: QTextCharFormat) -> float:
    if fmt.fontLetterSpacingType() == QFont.SpacingType.AbsoluteSpacing:
        return fmt.fontLetterSpacing()
    return 0.0


def _block_chars(block: QTextBlock) -> list[_Char]:
    chars: list[_Char] = []
    it = block.begin()
    index = 0
    while not it.atEnd():
        fragment = it.fragment()
        fmt = fragment.charFormat()
        layout = layout_from_state(layout_state(fmt))
        spacing, baseline = _current_spacing(fmt), fmt.baselineOffset()
        bold, italic, caps = fmt.fontWeight() >= 600, fmt.fontItalic(), fmt.fontCapitalization()
        for offset, ch in enumerate(fragment.text()):
            chars.append(_Char(ch, fragment.position() + offset, index, fmt, layout, bold, italic, caps, spacing, baseline))
        index += 1
        it += 1
    return chars


def _measured(ch: str, caps: QFont.Capitalization) -> str:
    """Karakter seperti yang DIGAMBAR (preview menerapkan lower()/upper() sebelum mengukur)."""
    if caps == QFont.Capitalization.AllUppercase:
        mapped = ch.upper()
    elif caps == QFont.Capitalization.AllLowercase:
        mapped = ch.lower()
    else:
        return ch
    return mapped if len(mapped) == 1 else ch


def _segments(chars: list[_Char]) -> list[list[_Char]]:
    """Pecah blok di tiap ``<br>``; tiap baris tampil dimulai dari x = 0 sehingga dihitung terpisah."""
    segments: list[list[_Char]] = [[]]
    for item in chars:
        if item.ch == _LINE_SEPARATOR:
            segments.append([])
        else:
            segments[-1].append(item)
    return segments


def _with_effects(base: QTextCharFormat, spacing: float, baseline: float) -> QTextCharFormat:
    fmt = QTextCharFormat(base)
    if abs(spacing) > _EPSILON:
        fmt.setFontLetterSpacingType(QFont.SpacingType.AbsoluteSpacing)
        fmt.setFontLetterSpacing(spacing)
    else:
        fmt.clearProperty(QTextFormat.Property.FontLetterSpacing)
        fmt.clearProperty(QTextFormat.Property.FontLetterSpacingType)
    if abs(baseline) > _EPSILON:
        fmt.setBaselineOffset(baseline)
    else:
        fmt.clearProperty(QTextFormat.Property.TextBaselineOffset)
    return fmt


def vertical_extra(document: QTextDocument) -> float:
    """Ruang vertikal tambahan (px, atas + bawah) yang dipasang :func:`reflow_layout` agar teks yang digeser
    ``voffset`` tidak terpotong tepi editor. ``QTextEdit`` tidak menambah tinggi baris untuk baseline offset, persis
    seperti game, sehingga hanya baris pertama / terakhir yang butuh ruang ini."""
    margin = document.documentMargin()
    frame_format = document.rootFrame().frameFormat()
    return max(0.0, frame_format.topMargin() - margin) + max(0.0, frame_format.bottomMargin() - margin)


def reflow_layout(document: QTextDocument, font: QFont) -> bool:
    """Samakan efek visual semua blok dengan state tag-nya. ``True`` bila ada yang diubah.

    ``font`` = font dasar editor (ukuran piksel dan metrik glyph diambil darinya). Aman dipanggil berulang: tanpa
    selisih tidak ada yang ditulis, sehingga undo/redo tidak terganggu. Pemanggil bertanggung jawab menahan sinyal
    ``textChanged`` (perubahan format juga memancarkannya).
    """
    px = max(6, QFontInfo(font).pixelSize())
    fonts = RunFonts(font, px)
    line_height = fonts.get(False, False)[1].height()
    max_negative_indent = -document.documentMargin()

    char_ops: list[tuple[int, int, QTextCharFormat, float, float]] = []   # (awal, akhir, format asal, spacing, baseline%)
    indent_ops: list[tuple[int, float]] = []
    raise_px = lower_px = 0.0                                  # seberapa jauh teks naik / turun akibat voffset

    block = document.begin()
    while block.isValid():
        chars = _block_chars(block)
        has_state = any(not item.layout.is_plain for item in chars)
        has_effects = any(abs(item.spacing) > _EPSILON or abs(item.baseline) > _EPSILON for item in chars)
        current_indent = block.blockFormat().textIndent()
        if not (has_state or has_effects or abs(current_indent) > _EPSILON):
            block = block.next()
            continue

        for item in chars:
            raise_px = max(raise_px, item.layout.voffset * px)
            lower_px = max(lower_px, -item.layout.voffset * px)

        want_spacing: dict[int, float] = {}
        want_indent = 0.0
        for number, segment in enumerate(_segments(chars)):
            if not segment:
                continue
            advances: list[float] = []
            centers: list[float | None] = []
            for item in segment:
                metrics = fonts.get(item.bold, item.italic)[1]
                glyph = _measured(item.ch, item.caps)
                advances.append(metrics.horizontalAdvance(glyph))
                if glyph.isspace():
                    centers.append(None)                           # spasi tidak digambar → tanpa pemusatan tinta
                else:
                    ink = metrics.tightBoundingRect(glyph)
                    centers.append(ink.left() + ink.width() / 2.0)
            plan = plan_block_spacing([item.layout for item in segment], px, advances, centers)
            for item, trailing in zip(segment, plan.trailing):
                want_spacing[item.position] = trailing
            if number == 0:                                        # indent hanya berlaku pada baris pertama blok
                want_indent = max(plan.lead, max_negative_indent)

        previous_key: tuple[int, float, float] | None = None
        for item in chars:
            spacing = want_spacing.get(item.position, 0.0)
            baseline = item.layout.voffset * px / line_height * 100.0
            if abs(spacing - item.spacing) <= _EPSILON and abs(baseline - item.baseline) <= _EPSILON:
                previous_key = None
                continue
            key = (item.fragment, round(spacing, 4), round(baseline, 4))
            if previous_key == key and char_ops and char_ops[-1][1] == item.position:
                start, _end, base, sp, bl = char_ops[-1]
                char_ops[-1] = (start, item.position + 1, base, sp, bl)        # perluas op sebelumnya
            else:
                char_ops.append((item.position, item.position + 1, item.base, spacing, baseline))
            previous_key = key
        if abs(want_indent - current_indent) > _EPSILON:
            indent_ops.append((block.position(), want_indent))
        block = block.next()

    margin = document.documentMargin()
    want_top, want_bottom = margin + math.ceil(raise_px), margin + math.ceil(lower_px)
    root = document.rootFrame()
    frame_format = root.frameFormat()
    frame_changed = (abs(frame_format.topMargin() - want_top) > _EPSILON
                     or abs(frame_format.bottomMargin() - want_bottom) > _EPSILON)

    if not char_ops and not indent_ops and not frame_changed:
        return False

    cursor = QTextCursor(document)
    cursor.joinPreviousEditBlock()
    try:
        for start, end, base, spacing, baseline in char_ops:
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            cursor.setCharFormat(_with_effects(base, spacing, baseline))
        for position, indent in indent_ops:
            cursor.setPosition(position)
            block_format = cursor.blockFormat()
            block_format.setTextIndent(indent)
            cursor.setBlockFormat(block_format)
        if frame_changed:
            frame_format.setTopMargin(want_top)
            frame_format.setBottomMargin(want_bottom)
            root.setFrameFormat(frame_format)
    finally:
        cursor.endEditBlock()
    return True


# ─────────────────────────────────────────────────────────────────────────────
#  Dialog nilai tag
# ─────────────────────────────────────────────────────────────────────────────
def ask_layout_value(parent: QWidget | None, tag: str, initial: str) -> str | None:
    """Minta nilai ``tag`` (px / em / %). ``None`` bila dibatalkan. Tombol OK baru aktif untuk nilai yang valid."""
    title, hint = LAYOUT_TAG_HELP[tag]
    dialog = QInputDialog(parent)
    dialog.setWindowTitle(f"Insert {tag} tag")
    dialog.setLabelText(f"{title}\n\n{hint}\n\nUnits: px (default), em, %")
    dialog.setTextValue(initial)
    line_edit = dialog.findChild(QLineEdit)
    if line_edit is not None:
        line_edit.setValidator(QRegularExpressionValidator(QRegularExpression(LENGTH_PATTERN), line_edit))
        line_edit.selectAll()
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return normalize_length_arg(dialog.textValue())
