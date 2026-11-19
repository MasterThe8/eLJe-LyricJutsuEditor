"""Pemindai Jutsu — mengenali blok Jutsu di script berdasarkan nilai Tick/Position yang berurutan.

Satu "Jutsu" adalah 3 atau 5 tick BERURUTAN (selisih 1) yang dihasilkan fitur Add Jutsu, Lyric Color no Jutsu
(method 1 & 2), dan Kan2Rom no Jutsu. Bentuk hasil keempat fitur itu (dicek dengan menjalankan operasinya):

    3 tick   lyric · phrase_start · lyric                              Add (No SlideUp), Color/Kan2Rom (Show Next Phrase)
    5 tick   lyric · phrase_start · lyric · phrase_start · lyric       Add (Hide/Fake Next), Color/Kan2Rom (Hide/Add Next),
                                                                       Lyric Color method 1 (pos-4 … pos)

Hal-hal yang membuat "3/5 tick" tidak selalu sama dengan "3/5 baris":

* Lyric Color method 1 membiarkan ``phrase_start`` ASLI di tick terakhir, sehingga tick terakhir berisi dua baris
  (``phrase_start`` lalu ``lyric``) → 5 tick, 6 baris. Karena itu pengenalan dilakukan per TICK, bukan per baris.
* ``section`` bisa terselip di tick yang sama dengan baris pertama Jutsu (``assemble_color_script`` menyisipkannya
  setelah baris itu). Baris seperti ini "transparan": ikut tampil bila berada DI TENGAH Jutsu, tetapi tidak dihitung
  dan tidak pernah menjadi baris pertama/terakhir.

Modul ini murni Python (tanpa import GUI). Ia hanya MEMBACA script; tidak mengubahnya.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.chart.events import ChartEvent, parse_event_line

# Jenis sebuah tick: "L" bila ada event lyric di tick itu, selain itu "P" (hanya phrase_start).
_LYRIC, _PHRASE = "L", "P"
PATTERN_3 = (_LYRIC, _PHRASE, _LYRIC)
PATTERN_5 = (_LYRIC, _PHRASE, _LYRIC, _PHRASE, _LYRIC)
# 5 dicoba lebih dulu: ``L P L P L`` juga diawali ``L P L`` (pola 3).
_PATTERNS = (PATTERN_5, PATTERN_3)


@dataclass(frozen=True)
class JutsuBlock:
    """Satu Jutsu di dalam script.

    Attributes:
        index:       Nomor urut Jutsu (0-based) menurut urutan kemunculan di script.
        start_line:  Indeks baris pertama (0-based) di ``script.splitlines()``.
        end_line:    Indeks baris sesudah baris terakhir (eksklusif), seperti ``range``.
        start_tick:  Tick pertama.
        end_tick:    Tick terakhir.
        tick_count:  3 atau 5.
        lines:       Baris-baris script milik Jutsu ini, apa adanya (termasuk ``section`` yang terselip).
    """

    index: int
    start_line: int
    end_line: int
    start_tick: int
    end_tick: int
    tick_count: int
    lines: tuple[str, ...]

    @property
    def text(self) -> str:
        """Seluruh baris Jutsu, dipisah ``\\n`` (tanpa newline di akhir)."""
        return "\n".join(self.lines)

    @property
    def last_line(self) -> str:
        """Baris lirik TERAKHIR Jutsu — mis. ``217 = E "lyric Lirik"``.

        Jutsu selalu berakhir di baris ``lyric``; bila (tidak lazim) tidak ada, dipakai baris terakhir apa adanya.
        """
        for line in reversed(self.lines):
            event = parse_event_line(line)
            if event is not None and event.is_lyric:
                return line
        return self.lines[-1]

    @property
    def key(self) -> tuple[int, int]:
        """Identitas stabil antar-pemindaian (mis. untuk mengingat item mana yang sedang terbuka)."""
        return (self.start_tick, self.end_tick)


@dataclass
class _Entry:
    """Satu baris event di dalam sebuah run, beserta apakah ia ikut membentuk Jutsu."""

    line_index: int
    event: ChartEvent
    counts: bool            # True: lyric / phrase_start. False: transparan (section, dll. di tick yang sama)


# ─────────────────────────────────────────────────────────────────────────────
#  Langkah 1 — kumpulkan "run": baris-baris yang tick-nya berurutan
# ─────────────────────────────────────────────────────────────────────────────
def _collect_runs(lines: list[str]) -> list[list[_Entry]]:
    """Potong script menjadi run. Satu run = baris-baris bersebelahan yang tick-nya naik 0 atau 1 tiap baris.

    * Selisih 0 (tick sama) selalu melanjutkan run; selisih 1 melanjutkan run hanya untuk lyric / phrase_start.
    * Baris yang bukan event valid (kosong, rusak, header) memutus run.
    * Run hanya dimulai oleh lyric / phrase_start.
    """
    runs: list[list[_Entry]] = []
    run: list[_Entry] = []

    for index, line in enumerate(lines):
        event = parse_event_line(line)
        if event is None:
            if run:
                runs.append(run)
                run = []
            continue

        entry = _Entry(index, event, counts=event.is_lyric or event.is_phrase_start)

        if run:
            delta = event.position - run[-1].event.position
            if delta == 0 or (delta == 1 and entry.counts):
                run.append(entry)
                continue
            runs.append(run)
            run = []

        if entry.counts:
            run.append(entry)

    if run:
        runs.append(run)
    return runs


# ─────────────────────────────────────────────────────────────────────────────
#  Langkah 2 — pecah satu run menjadi Jutsu (3 / 5 tick)
# ─────────────────────────────────────────────────────────────────────────────
def _group_by_tick(run: list[_Entry]) -> list[list[_Entry]]:
    groups: list[list[_Entry]] = []
    for entry in run:
        if groups and groups[-1][-1].event.position == entry.event.position:
            groups[-1].append(entry)
        else:
            groups.append([entry])
    return groups


def _tick_kind(group: list[_Entry]) -> str:
    """Tick yang memuat lyric = "L" (termasuk tick ``phrase_start`` + ``lyric`` milik Lyric Color 1)."""
    return _LYRIC if any(e.counts and e.event.is_lyric for e in group) else _PHRASE


def _trim(entries: list[_Entry]) -> list[_Entry]:
    """Buang baris transparan di ujung depan/belakang; yang di tengah dipertahankan."""
    start, end = 0, len(entries)
    while start < end and not entries[start].counts:
        start += 1
    while end > start and not entries[end - 1].counts:
        end -= 1
    return entries[start:end]


def _split_run(run: list[_Entry]) -> list[list[_Entry]]:
    """Run → daftar Jutsu (masing-masing daftar entry). Bagian yang tidak cocok pola 3/5 dilewati."""
    groups = _group_by_tick(run)
    kinds = tuple(_tick_kind(g) for g in groups)

    found: list[list[_Entry]] = []
    i = 0
    while i < len(groups):
        for pattern in _PATTERNS:
            n = len(pattern)
            if kinds[i:i + n] == pattern:
                entries = _trim([e for g in groups[i:i + n] for e in g])
                found.append(entries)
                i += n
                break
        else:
            i += 1
    return found


# ─────────────────────────────────────────────────────────────────────────────
#  API publik
# ─────────────────────────────────────────────────────────────────────────────
def find_jutsu_blocks(script: str) -> list[JutsuBlock]:
    """Semua Jutsu di ``script``, berurutan dari atas ke bawah. Script tanpa Jutsu → ``[]``."""
    lines = script.splitlines()
    blocks: list[JutsuBlock] = []

    for run in _collect_runs(lines):
        for entries in _split_run(run):
            first, last = entries[0], entries[-1]
            blocks.append(JutsuBlock(
                index=len(blocks),
                start_line=first.line_index,
                end_line=last.line_index + 1,
                start_tick=first.event.position,
                end_tick=last.event.position,
                tick_count=len(_group_by_tick(entries)),
                lines=tuple(lines[first.line_index:last.line_index + 1]),
            ))
    return blocks
