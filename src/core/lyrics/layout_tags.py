"""Tag tata letak TextMeshPro (``voffset`` / ``mspace`` / ``cspace``) — murni Python, tanpa GUI.

Modul ini adalah SATU sumber kebenaran untuk semantik ketiga tag tersebut. Dipakai bersama oleh:

* Live Lyrics Preview (``core.preview.phrase_display`` → ``ui.widgets.game_text.draw_text``),
* RichText editor di Jutsu Editor (``core.lyrics.renderer`` + ``ui.widgets.game_richtext``).

Semantik (diukur dari screenshot game, lihat ``core.preview.phrase_display``):

* ``<voffset=X>`` menggeser garis dasar teks; positif = naik. Tidak mengubah lebar maupun tinggi baris.
* ``<mspace=X>``  membuat tiap karakter memakai sel selebar X; TINTA glyph ditengahkan di sel
  (``<mspace=1>`` → huruf bertumpuk).
* ``<cspace=X>``  menambah X di belakang setiap karakter (termasuk yang terakhir).
* Satuan X: ``px`` (tanpa akhiran = piksel TextMeshPro), ``em``, atau ``%`` dari ukuran font. Semuanya
  dinormalkan menjadi pecahan em.

Qt rich text hanya punya padanan NATIVE untuk ``voffset`` (``baselineOffset``) dan ``cspace`` (letter spacing
absolut). ``mspace`` tidak punya padanan, jadi :func:`plan_block_spacing` menurunkannya menjadi letter spacing
per karakter dengan rumus yang SAMA dengan ``draw_text`` (sel tetap + tinta ditengahkan).
"""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

LAYOUT_TAGS: tuple[str, ...] = ("voffset", "mspace", "cspace")     # urutan kanonik saat ditulis ulang

# 1 "px" TextMeshPro = 1/TMP_UNITS_PER_EM em. DIUKUR dari screenshot game pengguna: ``<voffset=-0.5em>`` menggeser
# 41 px (→ 1 em ≈ 82 px) dan ``<cspace=10>`` menambah ≈ 25 px per huruf (→ 10 px ≈ 0.30 em). Toleransi ± beberapa
# persen karena sumbernya gambar; ubah di sini bila hasil ukur ulang berbeda.
TMP_UNITS_PER_EM = 33.0

LENGTH_PATTERN = r"[+-]?(?:\d+\.?\d*|\.\d+)\s*(?:px|em|%)?"     # juga dipakai validator input di UI
_LENGTH_RE = re.compile(r"([+-]?(?:\d+\.?\d*|\.\d+))\s*(px|em|%)?", re.IGNORECASE)


def parse_length(spec: str | None) -> float | None:
    """Argumen tag tata letak TextMeshPro → pecahan em. ``"-0.5em"`` → -0.5, ``"10"``/``"10px"`` →
    10 / ``TMP_UNITS_PER_EM``, ``"50%"`` → 0.5. Tidak valid → ``None``."""
    if not spec:
        return None
    m = _LENGTH_RE.fullmatch(spec.strip().strip("\"'").strip())
    if m is None:
        return None
    value, unit = float(m.group(1)), (m.group(2) or "px").lower()
    if unit == "em":
        return value
    if unit == "%":
        return value / 100.0
    return value / TMP_UNITS_PER_EM


def normalize_length_arg(spec: str | None) -> str | None:
    """Argumen valid → bentuk bersih untuk disimpan (spasi & tanda kutip pembungkus dibuang), selain itu ``None``.

    Penulisan pengguna dipertahankan (``.5em`` tetap ``.5em``) supaya membuka lalu menyimpan Jutsu tidak menulis
    ulang nilainya.
    """
    if parse_length(spec) is None:
        return None
    return spec.strip().strip("\"'").strip()          # type: ignore[union-attr]  (parse_length sudah menjamin str)


# ─────────────────────────────────────────────────────────────────────────────
#  State tag per karakter  <->  teks tooltip
# ─────────────────────────────────────────────────────────────────────────────
# Qt membuang baselineOffset dan letter spacing saat ``toHtml()``, tetapi tooltip format karakter selamat sebagai
# ``<span title="...">`` (dan ``title`` itu dibaca kembali oleh ``insertHtml``). Karena itu nilai mentah tag disimpan di
# tooltip: ia menjadi pembawa state yang lossless sekaligus tooltip hover di editor.
#
#     {"voffset": "0.5em", "cspace": "10"}  <->  "voffset=0.5em; cspace=10"
def encode_layout_state(state: Mapping[str, str]) -> str:
    """State tag → teks tooltip kanonik ('' bila tidak ada tag)."""
    return "; ".join(f"{name}={state[name]}" for name in LAYOUT_TAGS if name in state)


def decode_layout_state(text: str | None) -> dict[str, str]:
    """Tooltip → state tag. Teks yang BUKAN buatan editor ini (mis. ``title`` dari HTML tempelan) → ``{}``."""
    if not text:
        return {}
    state: dict[str, str] = {}
    for part in text.split(";"):
        name, sep, arg = part.partition("=")
        name, arg = name.strip().lower(), normalize_length_arg(arg)
        if not sep or name not in LAYOUT_TAGS or arg is None:
            return {}
        state[name] = arg
    return state


@dataclass(frozen=True, slots=True)
class CharLayout:
    """Efek tata letak efektif satu karakter, dalam pecahan em (sama dengan ``Run`` di Live Preview)."""

    voffset: float = 0.0                # positif = naik
    mspace: float | None = None         # lebar sel tetap; None = tanpa mspace
    cspace: float = 0.0                 # tambahan di belakang karakter

    @property
    def is_plain(self) -> bool:
        return not self.voffset and self.mspace is None and not self.cspace


PLAIN = CharLayout()


def layout_from_state(state: Mapping[str, str]) -> CharLayout:
    """State tag → :class:`CharLayout`. Aturan angka nol sama dengan ``phrase_display.build_display``:
    ``mspace=0`` berarti TANPA mspace."""
    return CharLayout(
        voffset=parse_length(state.get("voffset")) or 0.0,
        mspace=parse_length(state.get("mspace")) or None,
        cspace=parse_length(state.get("cspace")) or 0.0,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Perencanaan posisi karakter (padanan ``draw_text`` untuk rich text Qt)
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class BlockSpacing:
    """Hasil :func:`plan_block_spacing`.

    ``trailing[i]``: letter spacing (px) yang dipasang di karakter ke-i — tambahan setelah advance alaminya.
    ``lead``: geser awal baris pertama (px, bisa negatif) untuk karakter pertama, dipasang lewat indent blok.
    """

    trailing: tuple[float, ...]
    lead: float


def plan_block_spacing(layouts: Sequence[CharLayout], size_px: float, advances: Sequence[float],
                       ink_centers: Sequence[float | None]) -> BlockSpacing:
    """Hitung letter spacing per karakter agar tata letak Qt sama dengan ``ui.widgets.game_text.draw_text``.

    ``draw_text`` menaruh tiap karakter pada posisi IDEAL: karakter ber-``mspace`` menempati sel ``mspace*size_px``
    dengan tintanya ditengahkan di sel (``ink_centers[i]`` = jarak tengah tinta dari titik asal glyph; ``None`` untuk
    spasi → tidak digambar), karakter lain memakai advance alaminya. Setelahnya ditambah ``cspace*size_px``.

    Qt hanya bisa menambah jarak SETELAH sebuah karakter, jadi posisi ideal karakter ke-(i+1) dicapai dengan memberi
    karakter ke-i spacing ``ideal[i+1] - ideal[i] - advance[i]``. Karakter terakhir diberi spacing agar lebar total
    sama dengan ``draw_text`` (menentukan posisi teks yang mengikutinya). Pergeseran posisi karakter PERTAMA
    (``lead``) tidak bisa dibawa oleh karakter sebelumnya, sehingga dikembalikan terpisah.

    Seluruh panjang adalah piksel pada ukuran font yang sama; ketiga ``Sequence`` harus sama panjang.
    """
    count = len(layouts)
    if not (count == len(advances) == len(ink_centers)):
        raise ValueError("layouts, advances and ink_centers must have the same length")
    if count == 0:
        return BlockSpacing((), 0.0)

    ideal: list[float] = []
    x = 0.0
    for lay, advance, center in zip(layouts, advances, ink_centers):
        extra = lay.cspace * size_px
        if lay.mspace is not None:
            cell = lay.mspace * size_px
            ideal.append(x if center is None else x + cell / 2.0 - center)
            x += cell + extra
        else:
            ideal.append(x)
            x += advance + extra
    end = x

    trailing = [ideal[i + 1] - ideal[i] - advances[i] for i in range(count - 1)]
    trailing.append(end - ideal[-1] - advances[-1])
    return BlockSpacing(tuple(trailing), ideal[0])
