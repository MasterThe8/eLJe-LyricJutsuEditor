"""PhraseDisplay — mengubah satu ``PreviewPhrase`` menjadi *run* bergaya siap gambar.

Murni Python (tanpa GUI). Memakai aturan yang SUDAH ada di proyek, bukan salinan:

* ``core.lyrics.renderer.convert_symbols`` — aturan simbol (``-`` ``+`` ``#`` tak terlihat, ``_`` → spasi,
  ``=`` → ``-``). Dipakai HANYA pada teks di luar tag: memakainya pada string utuh merusak tag
  seperti ``<color=#FF0000>`` (``#`` dan ``=`` ikut diganti).
* ``core.operations.color_builders.WHITE`` — warna dasar bawaan.

Semantik tampilan (bukti: README Intro No Jutsu + kode Lyric Color Jutsu proyek ini):

* Seluruh phrase tampil sejak awal. Suku kata yang belum dinyanyikan memakai warna DASAR; begitu
  ``timestamp``-nya lewat ia berganti ke warna HIGHLIGHT dan tetap begitu sampai phrase berakhir.
* Tag warna: dua ``<color>`` bersarang → yang pertama warna dasar, yang kedua warna highlight.
  Satu ``<color>`` → warna itu dipakai di kedua keadaan. Tanpa tag → warna bawaan.
* Tag boleh membentang melewati beberapa suku kata (dibuka di satu lirik, ditutup di lirik lain),
  dan state tag tidak pernah bocor antar phrase.

Aturan gabung suku kata:

* Suku kata mendapat spasi di depannya kecuali suku kata *tampak* sebelumnya berakhir dengan ``-``
  (aturan ``events_to_lyric_lines``) atau ``=`` (spesifikasi format: "joins this syllable with the next").
* Penentuan itu memakai teks TANPA tag (``join_through_tags=True``): ``<b>al-</b>`` + ``ways`` →
  ``always``. Itu menyimpang dari ``events_to_lyric_lines`` (yang menganggap tag penutup sebagai
  huruf terakhir); set ``join_through_tags=False`` untuk perilaku persis tab Display Lyrics.
* ``_`` di game tampil sebagai spasi kosong (bukan hilang), jadi ia menghasilkan satu spasi " " tampak
  dan diperlakukan seperti suku kata tampak biasa.
* Suku kata yang tidak menghasilkan teks tampak (``+``, ``#``, ``-`` saja, kosong) tidak menambah spasi
  dan tidak mengubah keputusan gabung untuk suku kata berikutnya.

Tag tata letak TextMeshPro (``voffset`` / ``mspace`` / ``cspace``) — semantik diukur dari screenshot game:

* ``<voffset=X>`` menggeser garis dasar teks; positif = naik. Tidak mengubah lebar maupun tinggi baris.
* ``<mspace=X>`` membuat tiap karakter memakai lebar tetap X; tinta glyph DITENGAHKAN di sel itu
  (``<mspace=1>`` → huruf bertumpuk).
* ``<cspace=X>`` menambah X di belakang setiap karakter (termasuk yang terakhir).
* Satuan X: ``px`` (tanpa akhiran = piksel TextMeshPro), ``em``, atau ``%`` dari ukuran font. Semuanya disimpan
  sebagai pecahan em di ``Run`` supaya independen dari ukuran font; ``px`` → em lewat ``TMP_UNITS_PER_EM``
  (keduanya didefinisikan di ``core.lyrics.layout_tags``, dipakai juga oleh RichText editor Jutsu Editor).
* Tag bersarang: yang terdalam menang. Argumen yang tidak valid diabaikan (teks tetap tampil).

Teks lirik tetap utuh: spasi di dalam suku kata, Unicode, dan batas suku kata dipertahankan.
"""
from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache

from core.lyrics.layout_tags import TMP_UNITS_PER_EM, parse_length  # noqa: F401  (sumber tunggal; diekspor ulang)
from core.lyrics.renderer import convert_symbols
from core.operations.color_builders import WHITE
from core.preview.lyrics_parser import PreviewPhrase

Rgba = tuple[int, int, int, int]

_ZWSP = "\u200b"
JOIN_SUFFIXES = ("-", "=")        # "-": pasti (kode proyek + spesifikasi); "=": menurut spesifikasi format

_NAMED_COLORS: dict[str, Rgba] = {      # nama warna yang dikenali TextMeshPro
    "black": (0, 0, 0, 255), "blue": (0, 0, 255, 255), "green": (0, 128, 0, 255),
    "orange": (255, 128, 0, 255), "purple": (128, 0, 128, 255), "red": (255, 0, 0, 255),
    "white": (255, 255, 255, 255), "yellow": (255, 255, 0, 255),
}

_TAG_RE = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9-]*)(?:\s*=\s*([^<>]*?))?\s*>")
_LAYOUT_TAGS = frozenset({"voffset", "mspace", "cspace"})      # nilainya panjang (em), bukan warna
_FORMAT_TAGS = frozenset({"b", "i", "color", "lowercase", "uppercase"}) | _LAYOUT_TAGS
# Tag format TextMeshPro/Unity yang belum dirender: dibuang, teksnya tetap tampil.
_IGNORED_TAGS = frozenset({
    "smallcaps", "allcaps", "sub", "sup", "u", "s", "size", "font", "alpha",
    "align", "indent", "line-height", "margin", "nobr", "pos", "rotate", "space", "style", "width", "mark",
    "link", "page", "gradient", "sprite",
})


def parse_color(spec: str | None) -> Rgba | None:
    """``#RGB``, ``#RGBA``, ``#RRGGBB``, ``#RRGGBBAA`` (alpha DI AKHIR, gaya TextMeshPro) atau nama
    warna dasar. Tidak valid → ``None``."""
    if not spec:
        return None
    s = spec.strip().strip("\"'").strip().lower()
    if s in _NAMED_COLORS:
        return _NAMED_COLORS[s]
    if not s.startswith("#"):
        return None
    digits = s[1:]
    if len(digits) not in (3, 4, 6, 8) or any(c not in "0123456789abcdef" for c in digits):
        return None
    if len(digits) in (3, 4):
        digits = "".join(c * 2 for c in digits)
    if len(digits) == 6:
        digits += "ff"
    r, g, b, a = (int(digits[i:i + 2], 16) for i in range(0, 8, 2))
    return (r, g, b, a)


DEFAULT_BASE_COLOR: Rgba = parse_color(WHITE) or (255, 255, 255, 255)
# Default Fill Syllable Color
DEFAULT_SUNG_COLOR: Rgba = (252, 161, 1, 255)


@dataclass(frozen=True, slots=True)
class Run:
    """Potongan teks bergaya satu suku kata (atau pemisah spasi / baris baru)."""

    text: str                           # teks tampak (simbol sudah diproses, tanpa tag)
    syllable: int                       # indeks suku kata di ``phrase.lyrics`` pemilik run ini
    bold: bool = False
    italic: bool = False
    base_color: Rgba | None = None      # warna sebelum dinyanyikan (None = bawaan)
    sung_color: Rgba | None = None      # warna setelah dinyanyikan (None = bawaan)
    is_break: bool = False              # <br>
    voffset: float = 0.0                # em; positif = naik (``<voffset>``)
    mspace: float | None = None         # em; lebar sel tetap per karakter (``<mspace>``)
    cspace: float = 0.0                 # em; tambahan di belakang tiap karakter (``<cspace>``)

    @property
    def has_game_layout(self) -> bool:
        """True bila run memakai voffset/mspace/cspace (butuh penggambaran per karakter)."""
        return bool(self.voffset) or self.mspace is not None or bool(self.cspace)


@dataclass(frozen=True, slots=True)
class PhraseDisplay:
    runs: tuple[Run, ...]
    syllable_count: int

    @property
    def plain_text(self) -> str:
        """Teks tampak, ``\\n`` untuk <br> (untuk tes dan debugging)."""
        return "".join("\n" if r.is_break else r.text for r in self.runs)

    @property
    def is_empty(self) -> bool:
        return not any(r.is_break or r.text.strip() for r in self.runs)

    @property
    def has_game_layout(self) -> bool:
        return any(r.has_game_layout for r in self.runs)


# ─────────────────────────────────────────────────────────────────────────────
#  Tokenizer & pembangun
# ─────────────────────────────────────────────────────────────────────────────
def _tokenize(text: str) -> list[tuple]:
    """('text', s) | ('open', name, arg) | ('close', name) | ('br',). Tag tak dikenal tetap jadi teks."""
    tokens: list[tuple] = []
    pos = 0
    for m in _TAG_RE.finditer(text):
        closing, name, arg = m.group(1), m.group(2).lower(), m.group(3)
        if name == "br" and not closing:
            kind: tuple | None = ("br",)
        elif name in _FORMAT_TAGS:
            kind = ("close", name) if closing else ("open", name, arg)
        elif name in _IGNORED_TAGS:
            kind = ("skip",)
        else:
            continue                                  # bukan tag yang kita kenal → biarkan sebagai teks
        if m.start() > pos:
            tokens.append(("text", text[pos:m.start()]))
        if kind != ("skip",):
            tokens.append(kind)
        pos = m.end()
    if pos < len(text):
        tokens.append(("text", text[pos:]))
    return tokens


def _visible(text: str) -> str:
    """Terapkan aturan simbol proyek, lalu buang ZWSP (penanda 'tak terlihat' untuk HTML; di kanvas
    ZWSP bisa tergambar sebagai kotak pada font yang tidak punya glyph-nya).

    ``_`` di game tidak hilang melainkan tampil sebagai spasi kosong, jadi ia diubah menjadi " "
    (``underscore_as_space``) — hanya ``-`` yang benar-benar tak terlihat."""
    return convert_symbols(text, underscore_as_space=True).replace(_ZWSP, "")


def _plain(text: str, *, through_tags: bool) -> str:
    if not through_tags:
        return text
    return "".join(t[1] for t in _tokenize(text) if t[0] == "text")


def build_phrase_display(phrase: PreviewPhrase, *, join_through_tags: bool = True) -> PhraseDisplay:
    return build_display([lyric.text for lyric in phrase.lyrics], join_through_tags=join_through_tags)


def build_display(texts: Sequence[str], *, join_through_tags: bool = True) -> PhraseDisplay:
    """Bangun ``PhraseDisplay`` dari teks suku kata mentah (satu phrase). Dipakai Live Preview (lewat
    ``build_phrase_display``) dan judul Jutsu (satu suku kata) agar keduanya memakai aturan yang sama."""
    runs: list[Run] = []
    stack: list[tuple[str, object]] = []              # tag terbuka: (nama, nilai: Rgba untuk color, em untuk tag tata letak)
    prev_plain: str | None = None                      # teks (tanpa simbol terproses) suku kata tampak terakhir
    any_visible = False

    def innermost(name: str) -> float | None:
        return next((v for n, v in reversed(stack) if n == name and v is not None), None)

    def style() -> tuple[bool, bool, str | None, Rgba | None, Rgba | None, float, float | None, float]:
        bold = any(n == "b" for n, _ in stack)
        italic = any(n == "i" for n, _ in stack)
        case = next((n for n, _ in reversed(stack) if n in ("lowercase", "uppercase")), None)
        colors = [c for n, c in stack if n == "color" and c is not None]
        base = colors[0] if colors else None
        sung = colors[1] if len(colors) > 1 else base
        return bold, italic, case, base, sung, innermost("voffset") or 0.0, innermost("mspace") or None, innermost("cspace") or 0.0

    for idx, text in enumerate(texts):
        new_runs: list[Run] = []
        syllable_visible = False
        for token in _tokenize(text):
            kind = token[0]
            if kind == "open":
                name = token[1]
                value = parse_color(token[2]) if name == "color" else parse_length(token[2]) if name in _LAYOUT_TAGS else None
                stack.append((name, value))
            elif kind == "close":
                for pos in range(len(stack) - 1, -1, -1):          # tutup tag terbuka dengan nama sama
                    if stack[pos][0] == token[1]:
                        del stack[pos]
                        break
            elif kind == "br":
                new_runs.append(Run("", idx, is_break=True))
            else:                                                    # text
                visible = _visible(token[1])
                if not visible:
                    continue
                bold, italic, case, base, sung, voffset, mspace, cspace = style()
                if case == "lowercase":
                    visible = visible.lower()
                elif case == "uppercase":
                    visible = visible.upper()
                new_runs.append(Run(visible, idx, bold, italic, base, sung, False, voffset, mspace, cspace))
                syllable_visible = True

        if syllable_visible:
            joined = prev_plain is not None and prev_plain.endswith(JOIN_SUFFIXES)
            if any_visible and not joined and not (runs and runs[-1].is_break):
                runs.append(Run(" ", idx))
            prev_plain = _plain(text, through_tags=join_through_tags)
            any_visible = True
        runs.extend(new_runs)

    return PhraseDisplay(tuple(runs), len(texts))


@lru_cache(maxsize=256)
def get_phrase_display(phrase: PreviewPhrase) -> PhraseDisplay:
    """Versi ber-cache (kunci = isi phrase): dipanggil tiap frame tanpa membangun ulang."""
    return build_phrase_display(phrase)
