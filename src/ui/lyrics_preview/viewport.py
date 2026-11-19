"""Viewport lirik: dua panel translusen, highlight suku kata, dan transisi kincir air.

Lapisan Qt tipis. Semua keputusan ada di modul murni ``core.preview``:
    transition     → ``Scene``: item mana, di slot berapa, skala, alpha, berapa suku kata ter-highlight
    phrase_display → run bergaya;  phrase_layout → baris berposisi

Geometri: panel selebar widget, di tengah area (bukan posisi gameplay); proporsi di dalam panel diukur dari frame:
    panel atas  (baris SEKARANG)    gelap  (alpha ≈ 0.72)
    panel bawah (baris BERIKUTNYA)  0.457× panel atas, lebih terang (alpha ≈ 0.55); hilang bila tak ada baris berikutnya
    teks dipotong (clip) ke gabungan kedua panel, jadi baris yang keluar di atas / masuk dari bawah
    terpotong rapi, seperti pada game.
Transisi (Fade In / Slide Up / Fade Out) ditentukan oleh ``core.preview.transition``; panel latar ikut
memudar lewat ``Scene.visibility``.
Gerak: setiap item berada di "slot" bernilai riil (0 = tengah panel atas, 1 = tengah panel bawah); jarak
antar slot = jarak antar pusat panel. Item digambar dengan transform (translate + scale) dari satu tata
letak per phrase, sehingga tidak ada layout ulang per frame.

Widget ini hanya menerima ``Scene`` (``set_scene``); ia tidak mengenal audio atau timer.
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QTextOption
from PySide6.QtWidgets import QSizePolicy, QWidget

from core.preview.phrase_display import (
    DEFAULT_BASE_COLOR,
    DEFAULT_SUNG_COLOR,
    PhraseDisplay,
    get_phrase_display,
)
from core.preview.phrase_layout import PhraseLayout, layout_phrase
from core.preview.transition import Scene
from ui.widgets.game_text import draw_text, measure_text
from ui.theme import Theme, theme_events, to_qcolor


@dataclass(frozen=True)
class LyricsStyle:
    """Parameter tampilan.

    Panel selebar widget dan di tengah area (fitur ini tidak mengikuti posisi di gameplay Clone Hero).
    Proporsi di dalam panel diukur dari frame Clone Hero: panel bawah 0.457 × panel atas, jarak antar pusat
    baris 0.686 × panel atas, font ≈ 0.83 × panel atas (kotak baris ≈ tinggi panel), baris berikutnya 0.50×.
    """

    panel_width_ratio: float = 0.058    # tinggi panel atas = rasio × lebar widget …
    panel_height_ratio: float = 0.20    # … dan tidak lebih dari rasio × tinggi area
    panel_min: float = 40.0
    panel_max: float = 140.0
    next_panel_ratio: float = 0.457     # terukur: panel bawah / panel atas
    slot_gap_ratio: float = 0.686       # terukur: jarak pusat baris sekarang→berikutnya / tinggi panel atas
    font_ratio: float = 0.83            # ukuran font / tinggi panel atas (terukur dari frame, sedikit diperbesar)
    panel_a_alpha: float = 0.72         # terukur dari luminansi
    panel_b_alpha: float = 0.55         # terukur dari luminansi
    side_margin: float = 0.03           # × lebar widget
    min_fit_scale: float = 0.45
    fit_step: float = 0.92
    show_status_caption: bool = True


DEFAULT_STYLE = LyricsStyle()


class _Block:
    """Satu phrase yang sudah ditata pada ukuran font 'sekarang'."""

    __slots__ = ("display", "layout", "px", "line_height", "ascent", "fonts")

    def __init__(self, display: PhraseDisplay, layout: PhraseLayout, px: int, line_height: float,
                 ascent: float, fonts: dict) -> None:
        self.display, self.layout, self.px = display, layout, px
        self.line_height, self.ascent, self.fonts = line_height, ascent, fonts

    @property
    def height(self) -> float:
        return self.line_height * max(1, len(self.layout.lines))


class LyricsViewport(QWidget):
    _BLOCK_CACHE_LIMIT = 24

    def __init__(self, parent=None, style: LyricsStyle = DEFAULT_STYLE) -> None:
        super().__init__(parent)
        self.setObjectName("lyricsViewport")
        self.setMinimumSize(320, 180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._style = style
        self._scene: Scene | None = None
        self._blocks: dict[tuple, _Block | None] = {}
        theme_events.changed.connect(self._on_theme_changed)

    def sizeHint(self) -> QSize:
        return QSize(720, 360)

    # ── API ──────────────────────────────────────────────────────────────
    def set_scene(self, scene: Scene | None) -> None:
        self._scene = scene
        self.update()

    # ── internal ─────────────────────────────────────────────────────────
    def _on_theme_changed(self, _theme_id: str = "") -> None:
        self._blocks.clear()
        self.update()

    def _font(self, px: int, bold: bool, italic: bool) -> QFont:
        font = QFont(self.font())
        font.setPixelSize(max(6, px))
        font.setBold(bold)
        font.setItalic(italic)
        return font

    def _geometry(self) -> dict:
        st = self._style
        w, h = float(self.width()), float(self.height())
        caption_h = 30.0 if st.show_status_caption else 0.0
        area_h = max(1.0, h - caption_h)
        panel_h = max(st.panel_min, min(st.panel_max, w * st.panel_width_ratio, area_h * st.panel_height_ratio))
        panel_h = min(panel_h, max(20.0, area_h * 0.45))          # jendela sangat pendek: jangan melebihi area
        next_h = panel_h * st.next_panel_ratio
        top = max(4.0, (area_h - panel_h - next_h) / 2.0)         # blok panel di tengah area (di atas caption)
        y0 = top + panel_h / 2.0                                  # pusat slot 0 (sekarang)
        return dict(w=w, h=h, vx=0.0, vw=w, caption_h=caption_h, panel_h=panel_h, next_h=next_h, top=top,
                    y0=y0, delta=panel_h * st.slot_gap_ratio, font_px=max(10, round(panel_h * st.font_ratio)),
                    avail_w=max(1.0, w * (1.0 - 2.0 * st.side_margin)))

    def _block(self, phrase, px: int, avail_w: float, max_h: float) -> _Block | None:
        """Tata phrase pada ukuran 'sekarang': kecilkan font sampai muat lebar dan tinggi panel; bila
        tetap tidak muat, pecah kata di batas suku kata. Di-cache per (phrase, ukuran)."""
        key = (phrase, px, round(avail_w), round(max_h))
        if key in self._blocks:
            return self._blocks[key]
        if len(self._blocks) >= self._BLOCK_CACHE_LIMIT:
            self._blocks.clear()
        self._blocks[key] = block = self._build_block(phrase, px, avail_w, max_h)
        return block

    def _build_block(self, phrase, px: int, avail_w: float, max_h: float) -> _Block | None:
        display = get_phrase_display(phrase)
        if display.is_empty:
            return None
        st = self._style
        scale, break_words = 1.0, False
        while True:
            size = max(6, round(px * scale))
            fonts: dict[tuple[bool, bool], tuple[QFont, QFontMetricsF]] = {}
            cache: dict[tuple, float] = {}

            def metrics(bold: bool, italic: bool, _size=size, _fonts=fonts):
                k = (bold, italic)
                if k not in _fonts:
                    f = self._font(_size, bold, italic)
                    _fonts[k] = (f, QFontMetricsF(f))
                return _fonts[k]

            def measure(text: str, bold: bool, italic: bool, _m=metrics, _c=cache) -> float:
                k = (text, bold, italic)
                if k not in _c:
                    _c[k] = _m(bold, italic)[1].horizontalAdvance(text)
                return _c[k]

            def measure_spaced(text: str, bold: bool, italic: bool, mspace, cspace,
                               _m=metrics, _c=cache, _size=size) -> float:
                k = (text, bold, italic, mspace, cspace)
                if k not in _c:
                    _c[k] = measure_text(_m(bold, italic)[1], text, _size, mspace, cspace)
                return _c[k]

            layout = layout_phrase(display, avail_w, measure, break_long_words=break_words,
                                   measure_spaced=measure_spaced)
            regular_metrics = metrics(False, False)[1]         # sekaligus meng-cache font regular
            line_height = regular_metrics.height()
            # Satu baris boleh 'mengisi' panel (yang penuh pada game adalah tinta glyph, bukan kotak baris);
            # hanya phrase multi-baris yang dikecilkan agar tidak meluber jauh dari panel.
            too_tall = len(layout.lines) > 1 and line_height * len(layout.lines) > max_h * 1.25
            if not (layout.overflow or too_tall) or break_words:
                break
            if scale * st.fit_step < st.min_fit_scale:
                break_words = True            # sudah sekecil mungkin: pecah di batas suku kata
            else:
                scale *= st.fit_step

        return _Block(display, layout, size, line_height, regular_metrics.ascent(), fonts)

    def _draw_item(self, p: QPainter, item, geo: dict) -> None:
        block = self._block(item.phrase, geo["font_px"], geo["avail_w"], geo["panel_h"] * 0.96)
        if block is None or item.alpha <= 0.0:
            return
        p.save()
        p.setOpacity(max(0.0, min(1.0, item.alpha)))
        p.translate(geo["vx"] + geo["vw"] / 2.0, geo["y0"] + item.slot * geo["delta"])
        p.scale(item.scale, item.scale)
        y = -block.height / 2.0
        for line in block.layout.lines:
            x0 = -line.width / 2.0
            for placed in line.items:
                run = block.display.runs[placed.run_index]
                is_sung = run.syllable < item.sung
                r, g, b, a = (run.sung_color or DEFAULT_SUNG_COLOR) if is_sung else (run.base_color or DEFAULT_BASE_COLOR)
                font = block.fonts.get((run.bold, run.italic))
                if font is None:
                    font = self._font(block.px, run.bold, run.italic)
                    metrics = QFontMetricsF(font)
                else:
                    font, metrics = font
                p.setFont(font)
                p.setPen(QColor(r, g, b, a))
                draw_text(p, metrics, placed.text, x0 + placed.x, y + block.ascent, block.px,
                          voffset=run.voffset, mspace=run.mspace, cspace=run.cspace)
            y += block.line_height
        p.restore()

    def _caption(self) -> str:
        sc = self._scene
        if sc is None:
            return ""
        if sc.animating:
            label = {"fade_in": "Fade in", "slide_up": "Slide up", "fade_out": "Fade out"}[sc.kind.value]
            return f"{label} {round(sc.progress * 100):d}%"
        cur = sc.current
        if cur is None:
            return "No phrase"
        return f"Phrase #{cur.phrase.phrase_id + 1}  ·  syllable {cur.sung}/{len(cur.phrase.lyrics)}"

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.fillRect(self.rect(), to_qcolor(Theme.MOCK_SCREEN))

        st, sc = self._style, self._scene
        geo = self._geometry()

        if sc is not None and sc.items:
            panel_a = QRectF(geo["vx"], geo["top"], geo["vw"], geo["panel_h"])
            panel_b = QRectF(geo["vx"], geo["top"] + geo["panel_h"], geo["vw"], geo["next_h"])
            vis = max(0.0, min(1.0, sc.visibility))          # panel latar memudar bersama teks (Fade In / Fade Out)
            p.fillRect(panel_a, QColor(0, 0, 0, round(255 * st.panel_a_alpha * vis)))
            vis_b = vis * max(0.0, min(1.0, sc.next_visibility))   # tanpa baris berikutnya, panel bawah ikut hilang
            p.fillRect(panel_b, QColor(0, 0, 0, round(255 * st.panel_b_alpha * vis_b)))
            p.setClipRect(QRectF(geo["vx"], geo["top"], geo["vw"], geo["panel_h"] + geo["next_h"]))
            for item in sc.items:                      # urutan: keluar, naik, masuk (z-order tidak berpengaruh)
                self._draw_item(p, item, geo)
            p.setClipping(False)

        if st.show_status_caption and sc is not None:
            font = QFont(self.font())
            font.setPixelSize(max(11, min(int(geo["w"] / 56), 14)))
            p.setFont(font)
            p.setPen(to_qcolor(Theme.DIM))
            centered = QTextOption(Qt.AlignmentFlag.AlignHCenter)
            centered.setWrapMode(QTextOption.WrapMode.NoWrap)
            p.drawText(QRectF(geo["vx"], geo["h"] - geo["caption_h"], geo["vw"], geo["caption_h"] - 6),
                       self._caption(), centered)
        p.end()
