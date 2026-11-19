"""Accordion (Expandable List) untuk Jutsu Editor.

Susunannya::

    JutsuAccordionList (QListWidget)
     └─ QListWidgetItem  ──setItemWidget──▶  JutsuItemWidget (QWidget, QVBoxLayout)
                                              ├─ header: [QPushButton ▸/▾] [QLabel judul]
                                              └─ isi (hanya tampil saat expanded):
                                                   QTextEdit (lyric values saja)
                                                   QPlainTextEdit (seluruh script, bisa diedit)
                                                   [pesan error ·········· Revert  Apply]

Satu ``JutsuItemWidget`` = satu Jutsu (``JutsuBlock``). Judulnya adalah hasil render BARIS TERAKHIR Jutsu itu;
isi yang bisa dibuka-tutup adalah seluruh baris Jutsu. Widget TIDAK mengubah script sendiri: tombol Apply hanya
memancarkan ``apply_requested`` — pemilik (JutsuEditorWindow) yang meneruskannya ke editor utama.
"""
from __future__ import annotations

import re
from functools import partial

from PySide6.QtCore import QEvent, QSize, Qt, Signal, QSignalBlocker
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontInfo,
    QKeySequence,
    QPainter,
    QPalette,
    QShortcut,
    QTextCharFormat,
    QTextCursor,
    QTextDocumentFragment,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QColorDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.chart.events import parse_event_line
from core.lyrics.jutsu_model import JutsuLyricsDocument
from core.lyrics.layout_tags import LAYOUT_TAGS
from core.lyrics.tag_insert import TagInsertError, plan_tag_insertion
from core.lyrics.renderer import (
    jutsu_tags_to_richtext,
    render_lyrics_html,
    restore_symbols_from_display,
    richtext_to_jutsu_tags,
)
from core.lyrics.tags import TAG_SHORTCUTS
from core.operations.jutsu_scan import JutsuBlock
from core.preview.phrase_display import PhraseDisplay, build_display
from services.settings import SHORTCUTS
from ui.widgets.game_richtext import (
    apply_layout_tag,
    ask_layout_value,
    block_html,
    draft_html,
    layout_arg_at,
    reflow_layout,
    restore_draft_html,
    vertical_extra,
)
from ui.widgets.game_text import RunFonts, draw_text
from ui.theme import Theme, icon, mono_font
from ui.widgets.common import make_button, soft_wrap
from ui.widgets.highlighter import LyricHighlighter

BODY_MAX_LINES = 8          # tinggi isi dibatasi sekian baris; lebih dari itu di-scroll
BODY_FONT_SIZE = 12         # font cadangan bila pemilik belum memberi font editor utama (``set_editor_fonts``)
ITEM_BORDER = 2             # border 1px kiri+kanan/atas+bawah dari QListWidget#jutsuList::item (lihat stylesheet)
INVISIBLE_OPACITY = 0.2

_VISIBLE_STRIP = re.compile(r"<[^>]*>|[\s\u200b]")      # tag, spasi, dan zero-width space (hasil konversi "-" / "_")

# Label pendek untuk tombol insert tag di atas RichText editor. Nama lengkap
# dipakai di tooltip bersama hotkey-nya.
_TAG_BUTTON_TEXT = {
    "b": "Bold", "i": "Italic", "color": "Color", "br": "Break",
    "voffset": "VOffset", "smallcaps": "SCaps", "lowercase": "Lower",
    "uppercase": "Upper", "mspace": "MSpace", "cspace": "CSpace",
    "sub": "Sub", "sup": "Sup",
}
_TAG_BUTTON_LABEL = {
    "b": "Bold", "i": "Italic", "color": "Color", "br": "Line break",
    "voffset": "Vertical offset", "smallcaps": "Small caps", "lowercase": "Lowercase",
    "uppercase": "Uppercase", "mspace": "Monospace", "cspace": "Character spacing",
    "sub": "Subscript", "sup": "Superscript",
}


def _invisible_symbol_style() -> str:
    """CSS untuk simbol ``-``/``_``: terlihat samar (20%) di RichText editor."""
    color = QColor(Theme.EDITOR_TEXT)
    return f"color: rgba({color.red()}, {color.green()}, {color.blue()}, {INVISIBLE_OPACITY});"


def _py_index(text: str, qt_position: int) -> int:
    """Posisi kursor Qt (unit UTF-16) → indeks karakter Python. Beda hanya untuk karakter di luar BMP (mis. emoji)."""
    return len(text.encode("utf-16-le")[:2 * qt_position].decode("utf-16-le", errors="ignore"))


def _qt_index(text: str, index: int) -> int:
    """Indeks karakter Python → posisi kursor Qt (unit UTF-16)."""
    return len(text[:index].encode("utf-16-le", errors="surrogatepass")) // 2


def render_title_html(block: JutsuBlock) -> str:
    """HTML judul = baris lirik TERAKHIR Jutsu, lewat pipeline yang sama dengan tab Display Lyrics."""
    events_text = block.last_line
    # Judul meniru game: "_" tampil sebagai spasi kosong (bukan hilang). Editor RichText tetap
    # menampilkan "_" samar lewat ``invisible_style`` di ``_render_rich_events``.
    html = render_lyrics_html(
        events_text,
        apply_symbol_conversion=True,
        underscore_as_space=True,
    )
    if not _VISIBLE_STRIP.sub("", html):                    # mis. lirik kosong / hanya "-" atau "_" (tak terlihat)
        return f"<span style='color:{Theme.FAINT}'>(blank lyric)</span>"
    return html


def game_title_display(block: JutsuBlock) -> PhraseDisplay | None:
    """``PhraseDisplay`` judul bila lirik terakhir memakai tag tata letak game (voffset/mspace/cspace).

    Tag itu tidak punya padanan di Qt rich text (QLabel/QTextEdit), jadi judulnya digambar sendiri
    (``_GameTitleLabel``). Tanpa tag tersebut → ``None`` dan judul tetap lewat jalur HTML biasa.
    """
    event = parse_event_line(block.last_line)
    if event is None or not event.is_lyric:
        return None
    display = build_display([event.value])
    if display.is_empty or not display.has_game_layout:
        return None
    return display


def _chevron(open_: bool):
    return icon("chevron_down" if open_ else "chevron_right", "DIM", "TEXT")


class _ClickableLabel(QLabel):
    """QLabel yang memancarkan ``clicked`` — supaya klik pada judul juga membuka/menutup item."""
    clicked = Signal()

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()


class _GameTitleLabel(_ClickableLabel):
    """Judul yang menggambar sendiri teks ber-tag ``voffset``/``mspace``/``cspace`` seperti di game.

    Tanpa ``set_game_display`` ia berperilaku persis ``QLabel`` biasa (teks HTML).
    """
    _PAD = 4                                                # sama dengan ``+ 8`` pada tinggi minimum judul

    def __init__(self) -> None:
        super().__init__()
        self._display: PhraseDisplay | None = None

    def set_game_display(self, display: PhraseDisplay | None) -> None:
        self._display = display
        if display is not None:
            up, down = self._vertical_extra()
            self.setMinimumHeight(max(self.minimumHeight(),
                                      self.fontMetrics().lineSpacing() + 2 * self._PAD + round(up + down)))
        self.update()

    def _px(self) -> int:
        return max(6, QFontInfo(self.font()).pixelSize())

    def _vertical_extra(self) -> tuple[float, float]:
        """Seberapa jauh teks naik / turun dari kotak baris akibat ``voffset`` (px)."""
        if self._display is None:
            return 0.0, 0.0
        offsets = [run.voffset for run in self._display.runs if not run.is_break]
        px = self._px()
        return max(0.0, max(offsets, default=0.0)) * px, max(0.0, -min(offsets, default=0.0)) * px

    def paintEvent(self, event) -> None:
        if self._display is None:
            super().paintEvent(event)
            return
        px = self._px()
        fonts = RunFonts(self.font(), px)
        regular = fonts.get(False, False)[1]
        up, down = self._vertical_extra()
        top = (self.height() - (regular.height() + up + down)) / 2.0
        baseline = top + up + regular.ascent()
        default_color = self.palette().color(QPalette.ColorRole.WindowText)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        x = float(self.contentsRect().left())
        for run in self._display.runs:
            if run.is_break:                                # judul satu baris: <br> jadi spasi
                x += regular.horizontalAdvance(" ")
                continue
            font, metrics = fonts.get(run.bold, run.italic)
            color = run.sung_color or run.base_color        # sama dengan jalur HTML: <color> terdalam yang menang
            painter.setFont(font)
            painter.setPen(QColor(*color) if color else default_color)
            x = draw_text(painter, metrics, run.text, x, baseline, px,
                          voffset=run.voffset, mspace=run.mspace, cspace=run.cspace)
        painter.end()


class JutsuItemWidget(QWidget):
    """Container custom untuk satu Jutsu.

    Signal:
        toggled(bool)         setelah expand/collapse
        height_changed()      tinggi isi berubah karena jumlah baris yang diedit berubah
        apply_requested(str)  tombol Apply (atau Ctrl+Enter) ditekan; argumen = teks hasil edit
    """
    toggled = Signal(bool)
    height_changed = Signal()
    apply_requested = Signal(str)

    def __init__(self, block: JutsuBlock, parent: QWidget | None = None, *,
                 plain_font: QFont | None = None, rich_font: QFont | None = None):
        super().__init__(parent)
        self.setObjectName("jutsuItem")
        self.block = block
        # Font editor: mengikuti editor di jendela utama (PlainText Lyrics → Jutsu Script, Display Lyrics →
        # RichText Lyrics). Tanpa font dari pemilik, jatuh ke font mono bawaan.
        self._plain_font = QFont(plain_font) if plain_font is not None else mono_font(BODY_FONT_SIZE)
        self._rich_font = QFont(rich_font) if rich_font is not None else mono_font(BODY_FONT_SIZE)
        self._state = {"open": False}
        self.body: QWidget | None = None                    # dibuat malas: baru saat pertama kali dibuka
        self.text_edit: QPlainTextEdit | None = None
        self.rich_edit: QTextEdit | None = None
        self.lyric_document: JutsuLyricsDocument | None = None
        self._current_script = block.text
        self._syncing = False
        self._rich_sync_valid = True
        self._display_baseline: list[str] = []      # nilai setelah convert_symbols (yang tampil di RichText)
        self._raw_baseline: list[str] = []          # nilai raw sebelum convert_symbols
        self.tag_buttons: list[QToolButton] = []
        # Editor yang terakhir dipakai (RichText atau Jutsu Script): sasaran tombol insert tag di bawah RichText Lyrics.
        self._active_editor: QTextEdit | QPlainTextEdit | None = None
        self.rich_label: QLabel | None = None

        # ── header: tombol expand/collapse + judul ───────────────────────────
        self.toggle_btn = QPushButton()
        self.toggle_btn.setObjectName("jutsuToggle")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedSize(28, 28)
        self.toggle_btn.setIconSize(QSize(16, 16))
        self.toggle_btn.setToolTip("Expand / collapse")
        self.toggle_btn.setIcon(_chevron(False))            # tidak di-bind ke tema: window dibangun ulang saat tema berganti

        self.title = _GameTitleLabel()
        self.title.setObjectName("jutsuTitle")
        self.title.setTextFormat(Qt.TextFormat.RichText)
        self.title.setText(render_title_html(block))
        self.title.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title.setToolTip(
            f"Ticks {block.start_tick}–{block.end_tick}  ·  {block.tick_count} ticks  ·  "
            f"script lines {block.start_line + 1}–{block.end_line}")
        font = self.title.font()
        font.setPointSizeF(font.pointSizeF() + 2)
        self.title.setFont(font)
        soft_wrap(self.title, wrap=False)                   # lirik panjang tidak boleh melebarkan jendela
        self.title.setMinimumHeight(
            self.title.fontMetrics().lineSpacing() + 8
        )
        self.title.set_game_display(game_title_display(block))   # voffset/mspace/cspace digambar seperti di game
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)
        header.addWidget(self.toggle_btn)
        header.addWidget(self.title, 1)

        # ── susunan vertikal: header, lalu (opsional) isi ────────────────────
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(8, 6, 10, 16)
        self._root.setSpacing(6)
        self._root.addLayout(header)

        self.toggle_btn.clicked.connect(self.toggle)
        self.title.clicked.connect(self.toggle)

    # ── isi (RichText + PlainText + tombol) ─────────────────────────────────
    def _ensure_body(self) -> QWidget:
        if self.body is not None:
            return self.body

        rich_label = QLabel("RichText Lyrics")
        rich_label.setObjectName("jutsuSectionLabel")
        self.rich_label = rich_label

        rich_edit = QTextEdit()
        rich_edit.setObjectName("jutsuRichText")
        rich_edit.setAcceptRichText(True)
        rich_edit.setTabChangesFocus(True)
        rich_edit.setFont(self._rich_font)
        rich_edit.setPlaceholderText("Lyric event values will appear here")
        self.rich_edit = rich_edit
        tag_bar = self._build_tag_bar()

        plain_label = QLabel("Jutsu Script")
        plain_label.setObjectName("jutsuSectionLabel")

        edit = QPlainTextEdit(self.block.text)
        edit.setObjectName("jutsuText")
        edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        edit.setFont(self._plain_font)
        edit.setTabChangesFocus(True)
        edit.setPlaceholderText('Event lines, e.g.  768 = E "lyric Hold"')
        self._highlighter = LyricHighlighter(edit.document())
        self.text_edit = edit
        rich_edit.installEventFilter(self)                    # lacak editor aktif untuk tombol insert tag
        edit.installEventFilter(self)
        self._active_editor = rich_edit
        self._seen_text = edit.toPlainText()
        self.lyric_document = JutsuLyricsDocument.from_script(self._current_script)
        self._load_rich_from_model()

        self.error = QLabel("")
        self.error.setObjectName("errorNote")
        soft_wrap(self.error, wrap=False)
        self.revert_btn = make_button("Revert", "ghost")
        self.apply_btn = make_button("Apply", "primary")
        self.revert_btn.setToolTip("Discard your changes to this Jutsu")
        self.apply_btn.setToolTip("Apply to the editor and sort the script   Ctrl+Enter\n"
                                  "Undo with Ctrl+Z in the main editor.")
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 10, 0, 0)
        footer.setSpacing(8)
        footer.addWidget(self.error, 1)
        footer.addWidget(self.revert_btn)
        footer.addWidget(self.apply_btn)

        body = QWidget()
        body.setObjectName("jutsuBody")
        lay = QVBoxLayout(body)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.addWidget(rich_label)
        lay.addWidget(tag_bar)
        lay.addWidget(rich_edit)
        lay.addWidget(plain_label)
        lay.addWidget(edit)
        lay.addLayout(footer)
        body.hide()
        self._root.addWidget(body)
        self.body = body

        for target in (edit, rich_edit):
            for seq in ("Ctrl+Return", "Ctrl+Enter"):
                sc = QShortcut(QKeySequence(seq), target)
                sc.setContext(Qt.ShortcutContext.WidgetShortcut)
                sc.activated.connect(self._request_apply)
        for name, tag, attr in TAG_SHORTCUTS:
            sequence = QKeySequence(SHORTCUTS[name])
            for target, is_rich in ((rich_edit, True), (edit, False)):
                sc = QShortcut(sequence, target)
                sc.setContext(Qt.ShortcutContext.WidgetShortcut)
                sc.activated.connect(
                    lambda t=tag, a=attr, r=is_rich, w=target: self._insert_tag(w, t, a, rich=r)
                )
        self.apply_btn.clicked.connect(self._request_apply)
        self.revert_btn.clicked.connect(self.revert)
        edit.textChanged.connect(self._on_plain_text_changed)
        rich_edit.textChanged.connect(self._on_rich_text_changed)
        self._fit_edit_height()
        self._fit_rich_height()
        self._update_dirty()
        return body

    def _build_tag_bar(self) -> QWidget:
        """Kelompok tombol insert tag (dua baris) di bawah label RichText Lyrics.

        Satu-satunya bar tombol; tombolnya bekerja pada editor yang terakhir dipakai: format karakter bila
        RichText, markup literal bila Jutsu Script. Keduanya saling disinkronkan (``_on_plain_text_changed`` /
        ``_on_rich_text_changed``).
        """
        bar = QWidget()
        bar.setObjectName("jutsuTagBar")
        lay = QGridLayout(bar)
        lay.setContentsMargins(0, 0, 0, 2)
        lay.setHorizontalSpacing(4)
        lay.setVerticalSpacing(4)
        for index, (name, tag, attr) in enumerate(TAG_SHORTCUTS):
            btn = QToolButton(bar)
            btn.setObjectName("jutsuTagButton")
            btn.setText(_TAG_BUTTON_TEXT.get(tag, tag))
            shortcut = SHORTCUTS.get(name, "")
            tooltip = f"Insert {_TAG_BUTTON_LABEL.get(tag, tag)} tag"
            if tag in LAYOUT_TAGS or tag == "color":
                tooltip = f"Apply {_TAG_BUTTON_LABEL.get(tag, tag)} to the selection (asks for a value)"
            tooltip += "\nApplies to the editor you used last (RichText or Jutsu Script)"
            if shortcut:
                tooltip += f"   {shortcut}"
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setAutoRaise(True)
            btn.clicked.connect(lambda _checked=False, t=tag, a=attr: self._on_tag_button(t, a))
            row, column = divmod(index, 6)
            lay.addWidget(btn, row, column)
            self.tag_buttons.append(btn)
        lay.setColumnStretch(6, 1)
        return bar

    def _on_tag_button(self, tag: str, attr: str | None) -> None:
        target = self._active_editor if self._active_editor in (self.rich_edit, self.text_edit) else self.rich_edit
        self._insert_tag(target, tag, attr, rich=target is self.rich_edit)

    def eventFilter(self, watched, event) -> bool:  # noqa: N802 (Qt API)
        """Catat editor yang terakhir mendapat fokus; itulah sasaran tombol insert tag."""
        if event.type() == QEvent.Type.FocusIn and watched in (self.rich_edit, self.text_edit):
            self._active_editor = watched
        return super().eventFilter(watched, event)

    def _insert_tag(self, target: QTextEdit | QPlainTextEdit | None, tag: str,
                    attr: str | None, *, rich: bool) -> None:
        """Insert a lyric tag into ``target`` (RichText formatting or literal markup)."""
        if target is None or not target.isEnabled():
            return
        target.setFocus()
        if rich and tag in LAYOUT_TAGS:
            self._insert_rich_layout_tag(target, tag, attr)
            return
        if not rich:
            self._insert_plain_tag(target, tag, attr)
            return
        cursor = target.textCursor()
        cursor.beginEditBlock()
        try:
            if rich:
                self._insert_rich_tag(cursor, tag, attr)
            else:
                self._insert_literal_tag(cursor, tag, attr)
        finally:
            cursor.endEditBlock()
            target.setTextCursor(cursor)

    def _ask_color_value(self) -> str | None:
        """``#RRGGBB`` dari dialog warna (dipisah supaya tes bisa menggantinya)."""
        chosen = QColorDialog.getColor(QColor(Theme.EDITOR_TEXT), self, "Insert color tag")
        return chosen.name().upper() if chosen.isValid() else None

    def _insert_plain_tag(self, edit: QPlainTextEdit, tag: str, attr: str | None) -> None:
        """Tulis tag sebagai markup di Jutsu Script — hanya di dalam NILAI event ``lyric``.

        Rencananya dibuat ``core.lyrics.tag_insert.plan_tag_insertion``; di sini nilai tag ditanyakan dan hasilnya
        diterapkan sebagai SATU langkah undo. ``textChanged`` lalu merender ulang RichText (``_sync_plain_to_rich``).
        """
        void = attr is None                                             # <br>
        arg: str | None = None
        if tag == "color":
            arg = self._ask_color_value()
            if arg is None:
                return
        elif tag in LAYOUT_TAGS:
            arg = self._ask_layout_value(tag, (attr or "=0").lstrip("=") or "0")
            if arg is None:
                return

        script = edit.toPlainText()
        cursor = edit.textCursor()
        try:
            plan = plan_tag_insertion(
                script, _py_index(script, cursor.selectionStart()), _py_index(script, cursor.selectionEnd()),
                tag, arg, void=void)
        except TagInsertError as exc:
            self.show_error(str(exc))
            return

        edit.setFocus()
        cursor.beginEditBlock()
        try:
            for item in reversed(plan.edits):                           # dari belakang: posisi awal tetap valid
                cursor.setPosition(_qt_index(script, item.start))
                cursor.setPosition(_qt_index(script, item.end), QTextCursor.MoveMode.KeepAnchor)
                cursor.insertText(item.text)
        finally:
            cursor.endEditBlock()
        updated = edit.toPlainText()
        cursor.setPosition(_qt_index(updated, plan.select_start))
        if plan.select_end != plan.select_start:
            cursor.setPosition(_qt_index(updated, plan.select_end), QTextCursor.MoveMode.KeepAnchor)
        edit.setTextCursor(cursor)

    def _insert_rich_tag(self, cursor: QTextCursor, tag: str, attr: str | None) -> None:
        """Terapkan tag sebagai format RichText (round-trip lewat ``richtext_to_jutsu_tags``)."""
        if tag == "br":
            # U+2028 = line separator: QTextDocument menyimpannya sebagai <br>
            # DI DALAM paragraf, sehingga batas lyric event tidak berubah.
            cursor.insertText("\u2028")
            return

        if tag == "color":
            current = cursor.charFormat().foreground().color()
            if not current.isValid():
                current = QColor(Theme.EDITOR_TEXT)
            chosen = QColorDialog.getColor(current, self, "Insert color tag")
            if chosen.isValid():
                fmt = QTextCharFormat()
                fmt.setForeground(chosen)
                cursor.mergeCharFormat(fmt)
            return

        fmt = QTextCharFormat()
        if tag == "b":
            fmt.setFontWeight(QFont.Weight.Bold)
        elif tag == "i":
            fmt.setFontItalic(True)
        elif tag == "smallcaps":
            fmt.setFontCapitalization(QFont.Capitalization.SmallCaps)
        elif tag == "lowercase":
            fmt.setFontCapitalization(QFont.Capitalization.AllLowercase)
        elif tag == "uppercase":
            fmt.setFontCapitalization(QFont.Capitalization.AllUppercase)
        elif tag == "sub":
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignSubScript)
        elif tag == "sup":
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignSuperScript)
        else:
            # Tag tata letak (voffset/mspace/cspace) ditangani ``_insert_rich_layout_tag`` (butuh nilai dari pengguna);
            # sisanya, tag yang tidak dikenal, disisipkan sebagai markup literal agar tetap tersimpan di nilai lyric.
            self._insert_literal_tag(cursor, tag, attr)
            return
        cursor.mergeCharFormat(fmt)

    def _ask_layout_value(self, tag: str, initial: str) -> str | None:
        """Dialog nilai tag (dipisah supaya tes bisa menggantinya)."""
        return ask_layout_value(self, tag, initial)

    def _insert_rich_layout_tag(self, target: QTextEdit, tag: str, attr: str | None) -> None:
        """Terapkan ``voffset``/``mspace``/``cspace`` sebagai efek nyata di RichText (bukan teks literal).

        Nilai ditanyakan dulu (di luar edit block). Efek visualnya dipasang ``reflow_layout`` lewat
        ``_on_rich_text_changed``, memakai rumus yang sama dengan Live Lyrics Preview.
        """
        cursor = target.textCursor()
        initial = layout_arg_at(cursor, tag) or (attr or "=0").lstrip("=") or "0"
        value = self._ask_layout_value(tag, initial)
        if value is None:
            return
        cursor.beginEditBlock()
        try:
            apply_layout_tag(cursor, tag, value)
        finally:
            cursor.endEditBlock()
            target.setTextCursor(cursor)

    @staticmethod
    def _insert_literal_tag(cursor: QTextCursor, tag: str, attr: str | None) -> None:
        if attr is None:                                   # <br> tanpa penutup
            cursor.insertText(f"<{tag}>")
            return
        selected = cursor.selectedText()
        close = f"</{tag}>"
        cursor.insertText(f"<{tag}{attr}>{selected}{close}")
        if not selected:                                   # kursor masuk di antara tag
            cursor.movePosition(
                QTextCursor.MoveOperation.Left,
                QTextCursor.MoveMode.MoveAnchor,
                len(close),
            )

    def _render_rich_events(self, lyrics) -> None:
        """Bangun satu ``QTextBlock`` per lyric event.

        ``setHtml`` membuang paragraf yang kosong / hanya berisi spasi, sehingga
        jumlah blok bisa lebih sedikit dari jumlah event dan sinkronisasi
        RichText→PlainText langsung ditolak ("event boundaries changed").
        Membangun blok lewat ``QTextCursor`` menjamin jumlah blok selalu sama
        dengan jumlah event, termasuk untuk lirik kosong.
        """
        self.rich_edit.clear()
        cursor = self.rich_edit.textCursor()
        invisible_style = _invisible_symbol_style()
        for index, lyric in enumerate(lyrics):
            if index:
                cursor.insertBlock()
            rendered = jutsu_tags_to_richtext(
                lyric.raw_value,
                apply_symbol_conversion=True,
                invisible_style=invisible_style,
            )
            if rendered and not rendered.strip():
                # Spasi/tab saja: insertHtml akan menghilangkannya.
                cursor.insertText(rendered)
            else:
                cursor.insertHtml(rendered)
        self._reflow_rich()

    def _reflow_rich(self) -> None:
        """Pasang efek voffset/mspace/cspace dari state tag (lihat ``ui.widgets.game_richtext``)."""
        if self.rich_edit is None:
            return
        was_syncing, self._syncing = self._syncing, True          # perubahan format juga memancarkan textChanged
        try:
            reflow_layout(self.rich_edit.document(), self.rich_edit.font())
        finally:
            self._syncing = was_syncing

    def _load_rich_from_model(self) -> None:
        """Render one paragraph per lyric event, preserving event boundaries."""
        if self.rich_edit is None or self.lyric_document is None:
            return
        lyrics = self.lyric_document.lyrics
        self._raw_baseline = [lyric.raw_value for lyric in lyrics]
        self._rich_sync_valid = True

        self._syncing = True
        try:
            blocker = QSignalBlocker(self.rich_edit)
            self._render_rich_events(lyrics)
            del blocker
            self._display_baseline = self._rich_event_values() if lyrics else []
            self.rich_edit.setEnabled(bool(lyrics))
            for button in self.tag_buttons:
                button.setEnabled(bool(lyrics))
            # Tooltip widget menutupi tooltip per-karakter (nilai voffset/mspace/cspace), jadi petunjuk umum
            # ditaruh di label; widget hanya diberi tooltip bila tidak ada isi untuk di-hover.
            hint = "Each paragraph represents one lyric event. Use Shift+Enter for a line break inside an event."
            self.rich_edit.setToolTip("" if lyrics else "This Jutsu contains no editable lyric events.")
            if self.rich_label is not None:
                self.rich_label.setToolTip(hint)
        finally:
            self._syncing = False

    def _sync_plain_to_rich(self, text: str) -> None:
        """PlainText is authoritative for script structure; rebuild the lyric projection."""
        self.lyric_document = JutsuLyricsDocument.from_script(text)
        self._current_script = text
        self._load_rich_from_model()
        self.error.setText("")
        self._fit_rich_height()
        self._update_dirty()

    def _rich_event_values(self) -> list[str]:
        """Extract each QTextBlock independently so event boundaries cannot be merged silently."""
        document = self.rich_edit.document()
        values: list[str] = []
        block = document.begin()
        while block.isValid():
            cursor = QTextCursor(document)
            cursor.setPosition(block.position())
            cursor.setPosition(block.position() + block.length() - 1, QTextCursor.MoveMode.KeepAnchor)
            # block_html menyuntikkan state voffset/mspace/cspace langsung dari format karakter: ``toHtml()`` Qt
            # lama (mis. 6.8) tidak mengekspornya, sehingga tag tak pernah sampai ke Jutsu Script.
            fragment_html = block_html(block) or QTextDocumentFragment(cursor).toHtml()
            values.append(richtext_to_jutsu_tags(fragment_html))
            block = block.next()
        return values

    def _sync_rich_to_plain(self) -> None:
        """Update only lyric values; reject paragraph-count changes that lose event mapping."""
        if self.lyric_document is None:
            return
        lyrics = self.lyric_document.lyrics
        values = self._rich_event_values()
        if len(values) != len(lyrics):
            self._rich_sync_valid = False
            self.error.setText(
                "Lyric event boundaries changed. Use Shift+Enter for line breaks; "
                "do not add or remove paragraphs."
            )
            self.error.setToolTip(self.error.text())
            self._update_dirty()
            return

        updates = {}
        for index, (lyric, value) in enumerate(zip(lyrics, values)):
            display_base = (
                self._display_baseline[index]
                if index < len(self._display_baseline)
                else lyric.raw_value
            )
            raw_base = (
                self._raw_baseline[index]
                if index < len(self._raw_baseline)
                else lyric.raw_value
            )
            raw_value = restore_symbols_from_display(display_base, raw_base, value)
            if lyric.raw_value != raw_value:
                updates[lyric.source_line] = raw_value
        try:
            updated_script = self.lyric_document.update_values(updates)
        except (TypeError, ValueError) as exc:
            self._rich_sync_valid = False
            self.error.setText(f"Cannot synchronize lyrics: {exc}")
            self.error.setToolTip(str(exc))
            self._update_dirty()
            return

        self._rich_sync_valid = True
        self._current_script = updated_script
        # Rebuild the baseline model after every successful rich edit so its
        # stale-source validation compares against the latest canonical script.
        self.lyric_document = JutsuLyricsDocument.from_script(updated_script)
        # The RichText document still shows the display text from before this
        # sync (it is not re-rendered while typing). Refresh both baselines so
        # later edits are mapped against what is actually on screen now;
        # otherwise a stale display baseline can silently rewrite the user's
        # edit back to the old raw value (e.g. a typed "-" becomes "=" again).
        self._display_baseline = values
        self._raw_baseline = [lyric.raw_value for lyric in self.lyric_document.lyrics]
        if self.text_edit.toPlainText() != updated_script:
            blocker = QSignalBlocker(self.text_edit)
            self.text_edit.setPlainText(updated_script)
            del blocker
            self._seen_text = updated_script
        self.error.setText("")
        self._fit_edit_height()
        self._update_dirty()

    def _on_plain_text_changed(self) -> None:
        text = self.text_edit.toPlainText()
        if text == self._seen_text or self._syncing:
            return
        self._seen_text = text
        self._syncing = True
        try:
            self._sync_plain_to_rich(text)
        finally:
            self._syncing = False
        self._fit_edit_height()
        if self.expanded:
            self._relayout()
            self.height_changed.emit()

    def _on_rich_text_changed(self) -> None:
        if self._syncing:
            return
        self._syncing = True
        try:
            reflow_layout(self.rich_edit.document(), self.rich_edit.font())   # efek tag mengikuti isi yang baru
            self._sync_rich_to_plain()
        finally:
            self._syncing = False
        self._fit_rich_height()
        if self.expanded:
            self._relayout()
            self.height_changed.emit()

    def _relayout(self) -> None:
        """Hitung ulang layout SEKARANG (bersarang: isi dulu, lalu root) agar ``sizeHint()`` tidak basi."""
        if self.body is not None:
            self.body.layout().invalidate()
            self.body.layout().activate()
        self._root.invalidate()
        self._root.activate()

    def _fit_edit_height(self) -> bool:
        """Tinggi PlainText mengikuti jumlah baris (maks ``BODY_MAX_LINES``)."""
        edit = self.text_edit
        if edit is None:
            return False
        edit.ensurePolished()
        visible = max(1, min(max(edit.document().blockCount(), len(self.block.lines)), BODY_MAX_LINES))
        chrome = 2 * edit.document().documentMargin() + 2 * edit.frameWidth() + 8 + 14
        height = int(visible * edit.fontMetrics().lineSpacing() + chrome)
        if edit.height() == height and edit.minimumHeight() == height:
            return False
        edit.setFixedHeight(height)
        return True

    def _fit_rich_height(self) -> bool:
        """Tinggi RichText mengikuti jumlah lyric event (maks ``BODY_MAX_LINES``)."""
        edit = self.rich_edit
        if edit is None:
            return False
        edit.ensurePolished()
        count = max(1, min(edit.document().blockCount(), BODY_MAX_LINES))
        chrome = (2 * edit.document().documentMargin() + 2 * edit.frameWidth() + 8 + 14
                  + vertical_extra(edit.document()))               # ruang untuk teks yang digeser voffset
        height = int(count * edit.fontMetrics().lineSpacing() + chrome)
        if edit.height() == height and edit.minimumHeight() == height:
            return False
        edit.setFixedHeight(height)
        return True

    def set_editor_fonts(self, plain_font: QFont, rich_font: QFont) -> None:
        """Pakai font editor jendela utama: ``plain_font`` → Jutsu Script, ``rich_font`` → RichText Lyrics.

        Aman dipanggil kapan saja. Bila isi belum pernah dibuka, font hanya disimpan dan dipakai ``_ensure_body``.
        Font mengubah tinggi baris, jadi tinggi kedua editor dihitung ulang (tinggi item ikut lewat ``height_changed``).
        """
        plain_font, rich_font = QFont(plain_font), QFont(rich_font)
        if plain_font == self._plain_font and rich_font == self._rich_font:
            return
        self._plain_font, self._rich_font = plain_font, rich_font
        if self.body is None:
            return
        self.text_edit.setFont(plain_font)
        self.rich_edit.setFont(rich_font)
        self._reflow_rich()                                 # efek tag bergantung pada ukuran & metrik font
        self._fit_edit_height()
        self._fit_rich_height()
        if self.expanded:
            self._relayout()
            self.height_changed.emit()

    # ── edit: dirty / revert / apply ────────────────────────────────────────
    @property
    def draft_text(self) -> str | None:
        """Canonical Jutsu script draft; None bila isi belum pernah dibuka."""
        return None if self.text_edit is None else self._current_script

    @property
    def is_dirty(self) -> bool:
        return self.text_edit is not None and self._current_script != self.block.text

    def _update_dirty(self) -> None:
        dirty = self.is_dirty
        self.apply_btn.setEnabled(dirty and self._rich_sync_valid)
        self.revert_btn.setEnabled(dirty or not self._rich_sync_valid)

    def set_draft(
        self,
        text: str,
        rich_html: str | None = None,
        sync_error: str = "",
    ) -> None:
        """Pulihkan script draft dan, bila perlu, state RichText yang belum valid."""
        self._ensure_body()
        self._syncing = True
        try:
            blocker = QSignalBlocker(self.text_edit)
            self.text_edit.setPlainText(text)
            del blocker
            self._seen_text = text
            self._sync_plain_to_rich(text)
            if rich_html is not None:
                blocker = QSignalBlocker(self.rich_edit)
                restore_draft_html(self.rich_edit, rich_html)
                del blocker
                self._reflow_rich()
                self._display_baseline = self._rich_event_values()
                self._rich_sync_valid = False
                self.error.setText(sync_error or "RichText event boundaries need correction.")
                self.error.setToolTip(self.error.text())
        finally:
            self._syncing = False
        self._fit_edit_height()
        self._fit_rich_height()
        self._update_dirty()

    def revert(self) -> None:
        if self.text_edit is not None:
            self.set_draft(self.block.text)
            self.error.setText("")

    def show_error(self, message: str) -> None:
        self._ensure_body()
        self.error.setText(message)
        self.error.setToolTip(message)

    def _request_apply(self) -> None:
        if self.is_dirty and self._rich_sync_valid:
            self.apply_requested.emit(self._current_script)

    # ── expand / collapse ───────────────────────────────────────────────────
    @property
    def expanded(self) -> bool:
        return self._state["open"]

    def set_expanded(self, expanded: bool) -> None:
        if expanded == self.expanded:
            return
        self._state["open"] = expanded
        self._ensure_body().setVisible(expanded)
        self.toggle_btn.setIcon(_chevron(expanded))
        self._relayout()
        self.toggled.emit(expanded)

    def toggle(self) -> None:
        self.set_expanded(not self.expanded)


class JutsuAccordionList(QListWidget):
    """Daftar Jutsu yang tiap barisnya bisa dibuka/ditutup dan diedit.

    Signal ``apply_requested(widget, text)``: Apply ditekan di ``widget`` (``widget.block`` = Jutsu aslinya).
    """
    apply_requested = Signal(object, str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("jutsuList")
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSpacing(3)
        self._rows: list[tuple[QListWidgetItem, JutsuItemWidget]] = []
        # Font editor utama; disimpan di sini karena daftar sering dibangun ulang (``set_blocks``).
        self._plain_font: QFont | None = None
        self._rich_font: QFont | None = None

    # ── isi daftar ──────────────────────────────────────────────────────────
    def set_blocks(self, blocks: list[JutsuBlock], expanded_keys: set | frozenset = frozenset(),
                   drafts: dict | None = None) -> None:
        """Bangun ulang daftar.

        ``expanded_keys``: item yang kuncinya ada di sini dibuka kembali.
        ``drafts``: hasil ``drafts()`` sebelumnya; draf dipulihkan hanya bila Jutsu-nya belum berubah.
        Posisi scroll dijaga.
        """
        drafts = drafts or {}
        bar = self.verticalScrollBar()
        scroll = bar.value()
        self.setUpdatesEnabled(False)
        try:
            self.clear()
            self._rows.clear()
            for block in blocks:
                item = QListWidgetItem(self)
                widget = JutsuItemWidget(block, plain_font=self._plain_font, rich_font=self._rich_font)
                item.setSizeHint(QSize(0, widget.sizeHint().height() + ITEM_BORDER))
                self.setItemWidget(item, widget)
                sync = partial(self._sync_height, item, widget)
                widget.toggled.connect(sync)
                widget.height_changed.connect(sync)
                widget.apply_requested.connect(partial(self.apply_requested.emit, widget))
                self._rows.append((item, widget))

                saved = drafts.get(block.key)
                if saved is not None and saved[0] == block.text:
                    widget.set_draft(
                        saved[1],
                        rich_html=saved[2] if len(saved) > 2 else None,
                        sync_error=saved[3] if len(saved) > 3 else "",
                    )
                if block.key in expanded_keys:
                    widget.set_expanded(True)
                else:
                    sync()
        finally:
            self.setUpdatesEnabled(True)
        bar.setValue(scroll)

    def set_editor_fonts(self, plain_font: QFont, rich_font: QFont) -> None:
        """Font editor jendela utama untuk semua item (sekarang dan yang dibangun ulang nanti).

        ``plain_font`` (PlainText Lyrics) → Jutsu Script; ``rich_font`` (Display Lyrics) → RichText Lyrics.
        """
        self._plain_font, self._rich_font = QFont(plain_font), QFont(rich_font)
        self.setUpdatesEnabled(False)
        try:
            for _item, widget in self._rows:
                widget.set_editor_fonts(self._plain_font, self._rich_font)
        finally:
            self.setUpdatesEnabled(True)

    def expanded_keys(self) -> set:
        return {w.block.key for _item, w in self._rows if w.expanded}

    def drafts(self) -> dict:
        """Simpan script draft; sertakan HTML RichText bila sinkronisasinya belum valid."""
        result = {}
        for _item, widget in self._rows:
            if not (widget.is_dirty or not widget._rich_sync_valid):
                continue
            rich_html = draft_html(widget.rich_edit) if not widget._rich_sync_valid else None
            sync_error = widget.error.text() if not widget._rich_sync_valid else ""
            result[widget.block.key] = (
                widget.block.text, widget.draft_text, rich_html, sync_error
            )
        return result

    def set_all_expanded(self, expanded: bool) -> None:
        for _item, widget in self._rows:
            widget.set_expanded(expanded)

    # ── tinggi item mengikuti isi ───────────────────────────────────────────
    @staticmethod
    def _sync_height(item: QListWidgetItem, widget: JutsuItemWidget, *_args) -> None:
        widget.ensurePolished()

        layout = widget.layout()
        if layout is not None:
            layout.activate()

        height = widget.sizeHint().height()

        item.setSizeHint(
            QSize(0, height + ITEM_BORDER + 4)
        )
