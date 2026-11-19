"""Tata letak phrase: memecah ``PhraseDisplay`` menjadi baris berposisi.

Murni Python (tanpa GUI). Lebar teks diukur lewat fungsi ``measure(text, bold, italic) -> float``
yang disuntikkan pemanggil (di aplikasi: ``QFontMetricsF``; di tes: fungsi palsu), sehingga seluruh
logika wrap teruji tanpa font sungguhan.

Aturan:

* ``<br>`` adalah pemisah baris keras.
* Pemisah baris lunak hanya di spasi. Spasi di awal/akhir baris dibuang (tidak ikut lebar/centering).
* Kata yang lebih lebar dari ``max_width`` dibiarkan meluap (``overflow=True``) agar pemanggil bisa
  mengecilkan font; bila ``break_long_words=True`` kata itu dipecah di batas run (suku kata) —
  tanpa menyisipkan tanda hubung.
* ``x`` tiap item relatif terhadap awal barisnya; pemanggil yang menengahkan (``(lebar - line.width) / 2``).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from core.preview.phrase_display import PhraseDisplay

Measure = Callable[[str, bool, bool], float]
# Untuk run ber-``mspace``/``cspace``: (teks, bold, italic, mspace_em | None, cspace_em) -> lebar. Opsional; bila tidak
# disuntikkan, run tersebut diukur dengan ``measure`` biasa (spasi tag diabaikan).
MeasureSpaced = Callable[[str, bool, bool, "float | None", float], float]
_SPLIT_RE = re.compile(r"(\s+)")


@dataclass(frozen=True, slots=True)
class PlacedRun:
    run_index: int          # indeks di ``PhraseDisplay.runs`` (untuk gaya + indeks suku kata)
    text: str
    x: float
    width: float


@dataclass(frozen=True, slots=True)
class LayoutLine:
    items: tuple[PlacedRun, ...]
    width: float


@dataclass(frozen=True, slots=True)
class PhraseLayout:
    lines: tuple[LayoutLine, ...]
    width: float            # lebar baris terlebar
    overflow: bool          # True bila ada baris yang melebihi max_width


@dataclass(slots=True)
class _Atom:
    run_index: int
    text: str
    width: float
    is_space: bool


def layout_phrase(display: PhraseDisplay, max_width: float, measure: Measure, *,
                  break_long_words: bool = False,
                  measure_spaced: MeasureSpaced | None = None) -> PhraseLayout:
    max_width = max(1.0, float(max_width))
    lines: list[LayoutLine] = []

    for segment in _hard_lines(display):
        atoms = _atoms(display, segment, measure, measure_spaced)
        lines.extend(_wrap(atoms, max_width, break_long_words))

    width = max((ln.width for ln in lines), default=0.0)
    return PhraseLayout(tuple(lines), width, width > max_width + 1e-6)


def _hard_lines(display: PhraseDisplay) -> list[list[int]]:
    segments: list[list[int]] = [[]]
    for i, run in enumerate(display.runs):
        if run.is_break:
            segments.append([])
        else:
            segments[-1].append(i)
    if len(segments) > 1 and not segments[-1]:        # <br> di ujung phrase tidak menambah baris kosong
        segments.pop()
    return segments


def _atoms(display: PhraseDisplay, run_indices: list[int], measure: Measure,
           measure_spaced: MeasureSpaced | None = None) -> list[_Atom]:
    atoms: list[_Atom] = []
    for i in run_indices:
        run = display.runs[i]
        spaced = measure_spaced is not None and (run.mspace is not None or bool(run.cspace))
        for chunk in _SPLIT_RE.split(run.text):
            if not chunk:
                continue
            width = (measure_spaced(chunk, run.bold, run.italic, run.mspace, run.cspace)
                     if spaced else measure(chunk, run.bold, run.italic))
            atoms.append(_Atom(i, chunk, width, chunk.isspace()))
    return atoms


def _words(atoms: list[_Atom]) -> list[list[_Atom]]:
    """Pecah menjadi token: kata (atom non-spasi berurutan) atau spasi (satu atom)."""
    tokens: list[list[_Atom]] = []
    for atom in atoms:
        if atom.is_space or not tokens or tokens[-1][0].is_space:
            tokens.append([atom])
        else:
            tokens[-1].append(atom)
    return tokens


def _wrap(atoms: list[_Atom], max_width: float, break_long_words: bool) -> list[LayoutLine]:
    if not atoms:
        return [LayoutLine((), 0.0)]

    lines: list[list[_Atom]] = []
    current: list[_Atom] = []
    current_w = 0.0
    pending: list[_Atom] = []                         # spasi yang menunggu kata berikutnya
    pending_w = 0.0

    def flush() -> None:
        nonlocal current, current_w
        if current:
            lines.append(current)
        current, current_w = [], 0.0

    for token in _words(atoms):
        if token[0].is_space:
            if current:                               # spasi di awal baris dibuang
                pending.extend(token)
                pending_w += sum(a.width for a in token)
            continue

        word_w = sum(a.width for a in token)
        if current and current_w + pending_w + word_w > max_width:
            flush()
            pending, pending_w = [], 0.0
        if current:
            current.extend(pending)
            current_w += pending_w
        pending, pending_w = [], 0.0

        if break_long_words and word_w > max_width and len(token) > 1:
            for atom in token:                        # pecah di batas run
                if current and current_w + atom.width > max_width:
                    flush()
                current.append(atom)
                current_w += atom.width
        else:
            current.extend(token)
            current_w += word_w

    flush()
    return [_place(atoms_in_line) for atoms_in_line in lines] or [LayoutLine((), 0.0)]


def _place(atoms: list[_Atom]) -> LayoutLine:
    items: list[PlacedRun] = []
    x = 0.0
    for atom in atoms:
        if not atom.is_space:
            items.append(PlacedRun(atom.run_index, atom.text, x, atom.width))
        x += atom.width
    return LayoutLine(tuple(items), x)
