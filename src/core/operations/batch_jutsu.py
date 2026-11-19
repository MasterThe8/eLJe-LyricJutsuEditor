"""Batch Jutsu — Add Jutsu untuk BANYAK baris sekaligus. Murni Python, tanpa import GUI.

Modul ini membaca input pengguna, mengambil baris-baris yang akan diubah ("target"), lalu menerapkan Add Jutsu
ke semuanya (``apply_batch_jutsu``). Fungsi ekstraksi (``parse_target_input``, ``extract_targets``) hanya MEMBACA
script; ``apply_batch_jutsu`` mengembalikan teks baru.

Tiga mode input
---------------
* ``Single Phrase`` — satu tick ``phrase_start``; target = seluruh isi phrase itu. Memakai ``get_lines``
  (pengambil phrase yang sama dengan Lyric Color / Kan2Rom), lalu ``section`` dibuang dan baris pertama
  wajib ``phrase_start`` (``require_phrase_start``), persis seperti Jutsu berbasis phrase lainnya.
* ``List``  — beberapa tick dipisah koma; tiap tick berdiri sendiri, urutan input dipertahankan.
* ``Range`` — ``awal - akhir`` (kedua ujung termasuk); hanya event yang benar-benar ada di rentang itu.

Apa itu "target"
----------------
Satu BARIS TABEL = satu TICK. Hanya event ``lyric`` dan ``phrase_start`` yang menjadi target; ``section``,
``phrase_end`` dan event lain tidak pernah menjadi target dan tidak disentuh. Karena ``phrase_start`` sering
berada di tick yang sama dengan lirik pertamanya (mis. ``1536 phrase_start`` + ``1536 lyric Where``), keduanya
digabung menjadi satu target; penerapan mengganti KEDUANYA dengan satu grup Jutsu. Nilai awal kolom
"Lyric Input" diambil dari event ``lyric`` di tick itu (kosong bila hanya ada ``phrase_start``).

Tiap target membawa ``line_indexes`` + ``lines`` (indeks dan teks asli di ``script.splitlines()``), sehingga
penerapan bisa memastikan editor belum berubah sebelum mengganti baris — pola yang sama dengan ``jutsu_edit``.

Tabel Lyric Input
-----------------
Kolom tabel bergantung pada Jutsu (``table_columns``): No SlideUp = Closing | Lyric Input; Hide / Fake =
Closing | Hide-atau-Fake | Lyric Input. Tick TIDAK menjadi kolom — UI menampilkannya sebagai header baris.
Nilai awal sel dihitung ``default_row_values``; hasil edit dibawa sebagai ``RowValues`` (satu per target, urutan
sama dengan ``targets``) dan diperiksa ``check_row_values`` (semua sel yang tampil wajib terisi, seperti kolom
Lyric / Fake lyric pada dialog Add Jutsu).

Penerapan ke script
-------------------
``apply_batch_jutsu`` mengubah SETIAP target menjadi grup 3 / 5 baris dengan memanggil ``build_add_jutsu_text``
(kode Add Jutsu yang sama, satu kali per baris tabel; Closing / Hide / Fake / Lyric diambil dari tabel). Urutannya:

  1. nilai tabel valid (``check_row_values``) dan jarak antar target aman (``check_tick_spacing``);
  2. baris target di script masih sama dengan saat dipilih (editor belum berubah);
  3. tidak ada event LAIN (yang bukan target) di tick +1 … akhir grup — bila ada → ``EventCollisionError``;
  4. baris asli target diganti grupnya di tempat yang sama, lalu script diurutkan STABIL menurut tick
     (``sort_script_by_position``), persis seperti Lyric Color / Kan2Rom / Jutsu Editor. Event non-target tidak
     dibuang; yang satu tick dengan target (mis. ``section``) tetap ada.

Fungsinya murni: mengembalikan teks baru atau melempar ``JutsuError`` — tidak pernah mengubah masukan, sehingga
editor tidak mungkin berakhir setengah berubah. Mengapa diurutkan: contoh di spec punya ``1536 section Intro`` SETELAH
``1536 phrase_start``; tanpa pengurutan ia akan tertinggal di bawah ``1538`` (melanggar §6.4).

Jarak tick minimal
------------------
Add Jutsu mengubah SATU baris menjadi 3 atau 5 baris (tick +0 … +4). Dua target yang tick-nya berjarak < 5
akan saling menimpa, jadi ``extract_targets`` melempar ``TickTooCloseError`` (turunan ``JutsuError``) yang
menyebut pasangan tick bermasalahnya. Pengecekan ini hanya membandingkan antar-TARGET; tabrakan dengan event
lain yang bukan target (mis. ``section`` di tick +2) ditangani saat penerapan (``EventCollisionError``, langkah 3).
"""
from __future__ import annotations

import re
from bisect import bisect_right
from dataclasses import dataclass
from enum import Enum

from core.chart.events import ChartEvent, parse_event_line
from core.operations.add_lyric import ADD_FAKE_NEXT, ADD_HIDE_NEXT, ADD_NO_SLIDEUP, build_add_jutsu_text
from core.operations.errors import JutsuError, MSG_POSITION_NOT_FOUND
from core.operations.script import (
    check_position_in_script,
    event_name_of,
    get_lines,
    line_position,
    require_phrase_start,
    sort_script_by_position,
    validate_events,
)

# Jarak minimal antar tick target. Add Jutsu memakai tick +0 … +4, jadi tick berikutnya harus >= +5.
MIN_TICK_GAP = 5
TARGET_EVENTS = ("lyric", "phrase_start")
_MAX_DIGITS = 12                                   # sama dengan validator posisi di dialog Add Jutsu
_MAX_PAIRS_SHOWN = 8                               # pasangan tick yang disebut di pesan error
MSG_BATCH_CHANGED = ("The chart changed after the lines were selected. "
                     "Click Input Lyric again to refresh the lines, then apply.")


class BatchMode(str, Enum):
    """Mode pemilihan target. Nilainya = teks di dropdown (pola yang sama dengan ``ADD_*``)."""

    SINGLE = "Single Phrase"
    LIST = "List"
    RANGE = "Range"


@dataclass(frozen=True)
class TargetSpec:
    """Input pengguna yang sudah di-parse.

    ``ticks``: SINGLE → ``(tick,)``; LIST → semua tick sesuai urutan input; RANGE → ``(awal, akhir)``.
    """

    mode: BatchMode
    ticks: tuple[int, ...]


@dataclass(frozen=True)
class BatchTarget:
    """Satu target (satu baris tabel Lyric Input) beserta asal-usulnya di script.

    Attributes:
        position:     Tick target (tetap dipertahankan sebagai tick awal grup Jutsu).
        line_indexes: Indeks baris (0-based) di ``script.splitlines()`` yang menjadi target di tick ini.
        lines:        Teks asli baris-baris itu, apa adanya (untuk memeriksa script belum berubah).
        lyric:        Nilai awal "Lyric Input" (lossless; kosong bila tidak ada event ``lyric`` di tick ini).
        has_lyric:    True bila di tick ini ada event ``lyric``.
    """

    position: int
    line_indexes: tuple[int, ...]
    lines: tuple[str, ...]
    lyric: str
    has_lyric: bool


@dataclass(frozen=True)
class RowValues:
    """Isi satu baris tabel Lyric Input (juga masukan pembangkit event).

    ``extra`` = Hide Lyric (Hide Next Phrase) atau Fake Lyric (Fake Next Phrase); kosong untuk No SlideUp.
    """

    closing: str
    extra: str
    lyric: str


@dataclass(frozen=True)
class TableColumn:
    """Satu kolom tabel: ``key`` = nama field ``RowValues``, ``title`` = judul kolom."""

    key: str
    title: str


class RowValueError(JutsuError):
    """Sel wajib yang kosong. ``row`` = indeks baris (0-based), ``key`` = field ``RowValues`` yang bermasalah."""

    def __init__(self, message: str, row: int, key: str) -> None:
        super().__init__(message)
        self.row = row
        self.key = key


class EventCollisionError(JutsuError):
    """Event baru bertabrakan dengan event lain. ``collisions`` = ((tick_awal_grup, tick_akhir_grup, baris), ...)."""

    def __init__(self, collisions: list[tuple[int, int, str]] | tuple[tuple[int, int, str], ...]) -> None:
        self.collisions = tuple(collisions)
        shown = [f"  {line}   (inside the new events {start} - {end})"
                 for start, end, line in self.collisions[:_MAX_PAIRS_SHOWN]]
        if len(self.collisions) > _MAX_PAIRS_SHOWN:
            shown.append(f"  … and {len(self.collisions) - _MAX_PAIRS_SHOWN} more")
        super().__init__("The new events would overlap existing events, so nothing was changed:\n\n"
                         + "\n".join(shown)
                         + "\n\nMove or remove those events, then try again.")


class TickTooCloseError(JutsuError):
    """Ada target dengan tick berjarak < ``MIN_TICK_GAP``. ``pairs`` = ((tick_a, tick_b), ...)."""

    def __init__(self, pairs: list[tuple[int, int]] | tuple[tuple[int, int], ...], min_gap: int = MIN_TICK_GAP) -> None:
        self.pairs = tuple(pairs)
        self.min_gap = min_gap
        super().__init__(_too_close_message(self.pairs, min_gap))


def _too_close_message(pairs: tuple[tuple[int, int], ...], min_gap: int) -> str:
    shown = [f"  {a} and {b}  ({b - a} tick{'s' if b - a != 1 else ''} apart)" for a, b in pairs[:_MAX_PAIRS_SHOWN]]
    if len(pairs) > _MAX_PAIRS_SHOWN:
        shown.append(f"  … and {len(pairs) - _MAX_PAIRS_SHOWN} more")
    return (f"Some lines are too close together (less than {min_gap} ticks apart).\n"
            "Add Jutsu turns each line into 3 or 5 lines, so they would overlap:\n\n"
            + "\n".join(shown)
            + "\n\nMove or exclude those lines, then try again.")


# ─────────────────────────────────────────────────────────────────────────────
#  Langkah 1 — baca input pengguna
# ─────────────────────────────────────────────────────────────────────────────
_RANGE_RE = re.compile(r"\s*([0-9]+)\s*[-\u2013]\s*([0-9]+)\s*")     # "-" atau en dash (hasil copy dari dokumen)


def _parse_tick(token: str) -> int:
    """Satu tick: hanya angka 0-9 (tanpa tanda, desimal, atau digit non-ASCII). Melempar JutsuError bila salah."""
    token = token.strip()
    if not token or len(token) > _MAX_DIGITS or not re.fullmatch(r"[0-9]+", token):
        raise JutsuError(f"Invalid tick value: {token!r}. Use whole numbers only (e.g. 1536).")
    return int(token)


def parse_target_input(mode: BatchMode, text: str) -> TargetSpec:
    """Teks isian → ``TargetSpec``. Melempar JutsuError (pesan siap tampil) bila kosong / salah format."""
    raw = (text or "").strip()

    if mode is BatchMode.SINGLE:
        if not raw:
            raise JutsuError("Enter the tick of a phrase_start event (e.g. 1536).")
        return TargetSpec(mode, (_parse_tick(raw),))

    if mode is BatchMode.LIST:
        if not raw:
            raise JutsuError("Enter at least one tick value, separated by commas (e.g. 1536, 1920, 2688).")
        parts = raw.split(",")
        if any(not p.strip() for p in parts):
            raise JutsuError("Invalid list: there is an empty value between commas. Example: 1536, 1920, 2688")
        ticks = tuple(_parse_tick(p) for p in parts)
        seen: set[int] = set()
        duplicates: list[int] = []
        for tick in ticks:
            if tick in seen and tick not in duplicates:
                duplicates.append(tick)
            seen.add(tick)
        if duplicates:
            raise JutsuError("Duplicate tick value in the list: " + ", ".join(map(str, duplicates)) + ".")
        return TargetSpec(mode, ticks)

    if mode is BatchMode.RANGE:
        if not raw:
            raise JutsuError("Enter a range as start - end (e.g. 1728 - 2304).")
        match = _RANGE_RE.fullmatch(raw)
        if match is None or any(len(g) > _MAX_DIGITS for g in match.groups()):
            raise JutsuError("Invalid range. Use the form: start - end (e.g. 1728 - 2304).")
        start, end = int(match.group(1)), int(match.group(2))
        if start > end:
            raise JutsuError(f"Range start ({start}) must not be greater than range end ({end}).")
        return TargetSpec(mode, (start, end))

    raise JutsuError(f"Unknown target mode: {mode!r}")


# ─────────────────────────────────────────────────────────────────────────────
#  Langkah 2 — ambil baris target
# ─────────────────────────────────────────────────────────────────────────────
def _build_targets(entries: list[tuple[int, str]]) -> list[BatchTarget]:
    """``(indeks, baris)`` → daftar target: hanya ``lyric`` / ``phrase_start``, digabung per tick.

    Urutan target = urutan kemunculan tick di ``entries``. Baris lain (section, phrase_end, dst.) diabaikan di
    sini tetapi tetap utuh di script. Dua event ``lyric`` di satu tick tidak bisa dipetakan ke satu baris tabel
    tanpa membuang salah satunya, jadi ditolak.
    """
    groups: dict[int, list[tuple[int, str, ChartEvent]]] = {}
    for index, line in entries:
        event = parse_event_line(line)
        if event is None or event.name not in TARGET_EVENTS:
            continue
        groups.setdefault(event.position, []).append((index, line, event))

    targets: list[BatchTarget] = []
    for tick, items in groups.items():
        lyrics = [event for _i, _l, event in items if event.is_lyric]
        if len(lyrics) > 1:
            raise JutsuError(f"Tick {tick} has more than one lyric event. "
                             "Batch Jutsu needs exactly one lyric per tick.")
        targets.append(BatchTarget(
            position=tick,
            line_indexes=tuple(i for i, _l, _e in items),
            lines=tuple(l for _i, l, _e in items),
            lyric=lyrics[0].value if lyrics else "",
            has_lyric=bool(lyrics),
        ))
    return targets


def _match_indexes(lines: list[str], collected: list[str], start: int) -> list[int]:
    """Indeks di ``lines`` untuk tiap elemen ``collected`` (subsekuens berurutan hasil ``get_lines``).

    ``get_lines`` hanya mengembalikan teks, bukan posisinya. Hasilnya selalu subsekuens script yang dimulai di
    event pertama yang tick-nya sama dengan posisi (``start``), sehingga pencocokan berurutan ini pasti tepat.
    """
    indexes: list[int] = []
    cursor = 0
    for i in range(start, len(lines)):
        if cursor < len(collected) and lines[i] == collected[cursor]:
            indexes.append(i)
            cursor += 1
    if cursor != len(collected):                       # tidak mungkin terjadi bila script valid; jangan menebak
        raise JutsuError("Could not locate the phrase lines in the script.")
    return indexes


def _extract_single(lines: list[str], position: int) -> list[BatchTarget]:
    # Urutan langkah sama dengan select_phrase(): posisi ada → semua baris valid → get_lines → buang section.
    if not check_position_in_script(lines, position):
        raise JutsuError(MSG_POSITION_NOT_FOUND)
    validate_events(lines)

    collected = get_lines(lines, position)
    start = next(i for i, line in enumerate(lines) if line_position(line) == position)
    indexes = _match_indexes(lines, collected, start)

    entries = [(i, line) for i, line in zip(indexes, collected) if event_name_of(line) != "section"]
    require_phrase_start([line for _i, line in entries])      # baris pertama phrase harus phrase_start
    return _build_targets(entries)


def _extract_list(lines: list[str], ticks: tuple[int, ...]) -> list[BatchTarget]:
    validate_events(lines)
    by_tick: dict[int, list[tuple[int, str]]] = {}
    for index, line in enumerate(lines):
        by_tick.setdefault(line_position(line), []).append((index, line))

    targets: list[BatchTarget] = []
    for tick in ticks:                                          # urutan input dipertahankan
        entries = by_tick.get(tick)
        if not entries:
            raise JutsuError(f"Position not found: {tick}.")
        found = _build_targets(entries)
        if not found:
            raise JutsuError(f"Tick {tick} has no lyric or phrase_start event to process.")
        targets.extend(found)
    return targets


def _extract_range(lines: list[str], start: int, end: int) -> list[BatchTarget]:
    validate_events(lines)
    entries = [(i, line) for i, line in enumerate(lines) if start <= line_position(line) <= end]   # ujung inklusif
    targets = _build_targets(entries)
    if not targets:
        raise JutsuError(f"No lyric or phrase_start events found between {start} and {end}.")
    return targets


def check_tick_spacing(targets: list[BatchTarget], min_gap: int = MIN_TICK_GAP) -> None:
    """Melempar ``TickTooCloseError`` bila ada dua tick target yang berjarak < ``min_gap``.

    Yang dibandingkan adalah tick yang sudah diurutkan, jadi urutan input (mode List) tidak berpengaruh.
    Cukup membandingkan tetangga: bila ada pasangan yang terlalu dekat, salah satunya pasti bertetangga.
    """
    ticks = sorted({t.position for t in targets})
    pairs = [(a, b) for a, b in zip(ticks, ticks[1:]) if b - a < min_gap]
    if pairs:
        raise TickTooCloseError(pairs, min_gap)


def extract_targets(script: str, spec: TargetSpec) -> list[BatchTarget]:
    """Ambil target dari ``script`` (teks editor) sesuai ``spec``. Tidak mengubah ``script``.

    Melempar JutsuError bila posisi tidak ada / bukan awal phrase / tidak ada target, atau
    ``TickTooCloseError`` bila ada target yang tick-nya terlalu dekat.
    """
    lines = script.splitlines()
    if spec.mode is BatchMode.SINGLE:
        targets = _extract_single(lines, spec.ticks[0])
    elif spec.mode is BatchMode.LIST:
        targets = _extract_list(lines, spec.ticks)
    elif spec.mode is BatchMode.RANGE:
        targets = _extract_range(lines, spec.ticks[0], spec.ticks[1])
    else:
        raise JutsuError(f"Unknown target mode: {spec.mode!r}")
    check_tick_spacing(targets)
    return targets


# ─────────────────────────────────────────────────────────────────────────────
#  Tabel Lyric Input — kolom, nilai awal, validasi sel
# ─────────────────────────────────────────────────────────────────────────────
_CLOSING = TableColumn("closing", "Closing Lyric")
_LYRIC = TableColumn("lyric", "Lyric Input")
_COLUMNS: dict[str, tuple[TableColumn, ...]] = {
    ADD_NO_SLIDEUP: (_CLOSING, _LYRIC),
    ADD_HIDE_NEXT: (_CLOSING, TableColumn("extra", "Hide Lyric"), _LYRIC),
    ADD_FAKE_NEXT: (_CLOSING, TableColumn("extra", "Fake Lyric"), _LYRIC),
}


def table_columns(jutsu: str) -> tuple[TableColumn, ...]:
    """Kolom tabel Lyric Input untuk *jutsu* (2 kolom untuk No SlideUp, 3 untuk Hide / Fake)."""
    try:
        return _COLUMNS[jutsu]
    except KeyError:
        raise JutsuError(f"Unknown Jutsu: {jutsu!r}") from None


def default_row_values(jutsu: str, target: BatchTarget, closing_lyric: str = "-",
                       hidden_lyric: str = "_") -> RowValues:
    """Nilai awal satu baris: Closing = ``closing_lyric``; Hide = ``hidden_lyric``; Fake = kosong;
    Lyric Input = lirik asli target (kosong bila targetnya hanya ``phrase_start``).

    ``closing_lyric`` / ``hidden_lyric`` berasal dari Lyric Setting, sama seperti pada Add Jutsu.
    """
    table_columns(jutsu)                                   # validasi nama Jutsu
    extra = hidden_lyric if jutsu == ADD_HIDE_NEXT else ""
    return RowValues(closing=closing_lyric, extra=extra, lyric=target.lyric)


def carry_over_values(default: RowValues, previous: RowValues, same_jutsu: bool) -> RowValues:
    """Pakai kembali isian pengguna sebelumnya saat tabel dibuka ulang untuk target yang sama.

    Closing dan Lyric Input selalu ikut dibawa. ``extra`` hanya dibawa bila Jutsu-nya tidak berganti,
    karena artinya berbeda (Hide ≠ Fake); bila berganti dipakai nilai default Jutsu baru.
    """
    return RowValues(closing=previous.closing,
                     extra=previous.extra if same_jutsu else default.extra,
                     lyric=previous.lyric)


def check_row_values(jutsu: str, targets: list[BatchTarget] | tuple[BatchTarget, ...],
                     values: list[RowValues] | tuple[RowValues, ...]) -> None:
    """Semua sel yang tampil di tabel wajib terisi (spasi saja dianggap kosong).

    Melempar ``RowValueError`` untuk sel kosong PERTAMA (urut baris, lalu kolom) agar UI bisa menyorotnya,
    atau ``JutsuError`` bila jumlah baris tidak sama dengan jumlah target.
    """
    columns = table_columns(jutsu)
    if len(values) != len(targets):
        raise JutsuError(f"The table has {len(values)} rows but {len(targets)} lines were selected.")
    for row, (target, value) in enumerate(zip(targets, values)):
        for column in columns:
            text = getattr(value, column.key)
            if not text.strip():
                raise RowValueError(f"Tick {target.position}: {column.title} must be filled in.", row, column.key)
            if "".join(text.splitlines()) != text:           # \n, \r, U+2028, dst. akan memecah baris event
                raise RowValueError(f"Tick {target.position}: {column.title} must be a single line.", row, column.key)


# ─────────────────────────────────────────────────────────────────────────────
#  Penerapan ke script
# ─────────────────────────────────────────────────────────────────────────────
def _generate_group(jutsu: str, target: BatchTarget, row: RowValues) -> list[str]:
    """Grup 3 / 5 baris untuk satu target — langsung dari ``build_add_jutsu_text`` (logika Add Jutsu)."""
    text = build_add_jutsu_text(jutsu, target.position, lyric=row.lyric, fake_lyric=row.extra,
                                closing_lyric=row.closing, hidden_lyric=row.extra)
    group = text.split("\n")
    for line in group:
        if parse_event_line(line) is None:                    # pengaman: jangan pernah menulis baris rusak
            raise JutsuError(f"Generated event is not valid: {line!r}")
    return group


def apply_batch_jutsu(script: str, jutsu: str, targets: list[BatchTarget] | tuple[BatchTarget, ...],
                      rows: list[RowValues] | tuple[RowValues, ...]) -> str:
    """Script baru (teks lengkap) setelah tiap target diganti grup Jutsu-nya. ``script`` tidak diubah.

    ``rows[i]`` adalah isian tabel untuk ``targets[i]``. Melempar ``JutsuError`` (atau turunannya:
    ``RowValueError``, ``TickTooCloseError``, ``EventCollisionError``) tanpa mengubah apa pun bila ada masalah.
    """
    targets, rows = list(targets), list(rows)
    if not targets:
        raise JutsuError("No lines were selected.")
    check_row_values(jutsu, targets, rows)
    ticks = [t.position for t in targets]
    duplicates = sorted({tick for tick in ticks if ticks.count(tick) > 1})
    if duplicates:
        raise JutsuError("Duplicate target position: " + ", ".join(map(str, duplicates)) + ".")
    check_tick_spacing(targets)

    lines = script.splitlines()
    validate_events(lines)

    # Editor harus masih sama dengan saat target dipilih (pola yang sama dengan Jutsu Editor).
    replaced: set[int] = set()
    for target in targets:
        if not target.line_indexes or len(target.line_indexes) != len(target.lines):
            raise JutsuError(MSG_BATCH_CHANGED)
        for index, line in zip(target.line_indexes, target.lines):
            if not 0 <= index < len(lines) or lines[index] != line:
                raise JutsuError(MSG_BATCH_CHANGED)
        replaced.update(target.line_indexes)

    groups: dict[int, list[str]] = {}                          # indeks baris pertama target → grup penggantinya
    spans: list[tuple[int, int]] = []
    for target, row in zip(targets, rows):
        group = _generate_group(jutsu, target, row)
        groups[min(target.line_indexes)] = group
        spans.append((target.position, target.position + len(group) - 1))

    # Tabrakan: event yang TIDAK diganti dan tick-nya jatuh di +1 … akhir grup. Satu tick dengan target
    # (mis. section) bukan tabrakan — memang sudah begitu di chart aslinya.
    kept = sorted(((line_position(line), line) for index, line in enumerate(lines) if index not in replaced),
                  key=lambda item: item[0])
    kept_ticks = [tick for tick, _line in kept]
    collisions = [(start, end, line)
                  for start, end in spans
                  for _tick, line in kept[bisect_right(kept_ticks, start):bisect_right(kept_ticks, end)]]
    if collisions:
        raise EventCollisionError(collisions)

    merged: list[str] = []
    for index, line in enumerate(lines):
        if index in groups:
            merged.extend(groups[index])
        elif index not in replaced:
            merged.append(line)
    result = "\n".join(sort_script_by_position(merged))
    if script.endswith(("\n", "\r")):                          # jaga newline penutup bila editor memilikinya
        result += "\n"
    return result
