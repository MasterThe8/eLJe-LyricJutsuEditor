"""Alat bantu bersama untuk Jutsu: membaca baris event dan memilih satu phrase.

"Script" di sini adalah daftar baris event di editor, misalnya::

    768 = E "phrase_start"
    768 = E "lyric Hold"
    864 = E "lyric the"

Fungsi-fungsi di file ini berasal dari method yang sama-namanya di Jutsu.py / LCJutsu.py / CCJutsu.py /
CnvrtJutsu.py lama (isinya identik di keempat file itu). Beberapa perilaku lama SENGAJA dipertahankan
persis, karena hasil akhirnya (spasi, urutan baris) bergantung padanya:

* ``event_data.strip('E "')`` membuang karakter ``E``, spasi, dan ``"`` dari KEDUA ujung (per karakter,
  bukan per kata). Akibatnya lirik yang berakhir huruf ``E`` / spasi ikut terpotong.
* Pengurutan memakai ``sorted`` yang stabil: baris dengan posisi sama tetap berurutan seperti saat dimasukkan.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.operations.errors import JutsuError, MSG_NOT_PHRASE_START, MSG_POSITION_NOT_FOUND

EVENT_SEPARATOR = " = "
NAME_STRIP_CHARS = 'E "'


# ─────────────────────────────────────────────────────────────────────────────
#  Membaca satu baris event
# ─────────────────────────────────────────────────────────────────────────────
def try_split_event(line: str) -> tuple[str, str] | None:
    """``'768 = E "lyric Hi"'`` → ``('768', 'E "lyric Hi"')``. None bila baris bukan ``<pos> = <data>``.

    Dipecah di " = " PERTAMA saja, sehingga lirik yang memuat " = " tidak merusak pembacaan.
    """
    parts = line.split(EVENT_SEPARATOR, 1)
    if len(parts) != 2:
        return None
    return parts[0], parts[1]


def split_event_line(line: str) -> tuple[str, str]:
    """Seperti ``try_split_event`` tetapi melempar JutsuError bila baris tidak valid."""
    parts = try_split_event(line)
    if parts is None:
        raise JutsuError(f"Not a valid event line: {line!r}")
    return parts


def parse_event_data(event_data: str) -> tuple[str, str]:
    """``'E "lyric Hold the"'`` → ``('lyric', 'Hold the')``; ``'E "phrase_start"'`` → ``('phrase_start', '')``."""
    event_name, *value = event_data.strip(NAME_STRIP_CHARS).split(" ")
    value = " ".join(value)
    return event_name, value


def event_name_of(line: str) -> str:
    """Nama event dari satu baris (``lyric``, ``phrase_start``, ``section``, ...). Baris tidak valid → ''."""
    parts = try_split_event(line)
    if parts is None:
        return ""
    return parts[1].strip(NAME_STRIP_CHARS).split(" ")[0]


def line_position(line: str) -> int:
    """Angka posisi di depan ``' = '`` (dipakai sebagai kunci sorting)."""
    return int(line.split(EVENT_SEPARATOR, 1)[0])


# ─────────────────────────────────────────────────────────────────────────────
#  Format baris event yang dibuat Jutsu
# ─────────────────────────────────────────────────────────────────────────────
def lyric_event(position: int, text: str) -> str:
    """``lyric_event(768, 'Hi')`` → ``768 = E "lyric Hi"``."""
    return str(position) + ' = E "lyric ' + text + '"'


def phrase_start_event(position: int) -> str:
    """``phrase_start_event(769)`` → ``769 = E "phrase_start"``."""
    return str(position) + ' = E "phrase_start"'


# ─────────────────────────────────────────────────────────────────────────────
#  Section
# ─────────────────────────────────────────────────────────────────────────────
def get_section_lines(script: list[str]) -> list[str]:
    """Semua baris ``section`` di seluruh script."""
    section_lines = []
    for line in script:
        if event_name_of(line) == "section":
            section_lines.append(line)
    return section_lines


def remove_section_lines(script: list[str]) -> list[str]:
    """Semua baris KECUALI ``section`` (baris yang tidak bisa dibaca tetap dipertahankan)."""
    filtered_script = []
    for line in script:
        parts = try_split_event(line)
        if parts is None:
            filtered_script.append(line)
        elif event_name_of(line) != "section":
            filtered_script.append(line)
    return filtered_script


def remove_elements(list1: list[str], list2: list[str]) -> list[str]:
    """``list1`` tanpa elemen yang sama persis dengan salah satu elemen ``list2`` (duplikat ikut terhapus)."""
    return [x for x in list1 if x not in list2]


# ─────────────────────────────────────────────────────────────────────────────
#  Mencari phrase
# ─────────────────────────────────────────────────────────────────────────────
def check_position_in_script(script: list[str], position: int) -> bool:
    """True bila ada baris yang diawali ``'<position> = '`` (tanpa spasi di depan)."""
    for line in script:
        if line.startswith(str(position) + EVENT_SEPARATOR):
            return True
    return False


def validate_events(script: list[str]) -> None:
    """Pastikan setiap baris berbentuk ``<angka> = <data>``; bila tidak, JutsuError menyebut nomor barisnya.

    Aplikasi lama langsung crash (ValueError) pada baris kosong / rusak; di sini dijadikan pesan yang jelas.
    """
    for number, line in enumerate(script, start=1):
        parts = try_split_event(line)
        try:
            if parts is None:
                raise ValueError
            int(parts[0])
        except ValueError:
            raise JutsuError(f"Line {number} is not a valid event: {line!r}") from None


def get_lines(events: list[str], position: int) -> list[str]:
    """Baris-baris milik phrase yang dimulai di ``position``.

    Mulai dikumpulkan dari event PERTAMA yang posisinya == ``position`` (apa pun jenisnya), lalu semua
    event sesudahnya ikut sampai bertemu ``phrase_start`` / ``phrase_end`` di posisi lain (event
    penghenti itu sendiri TIDAK ikut). ``phrase_start`` / ``phrase_end`` di posisi yang sama ikut terkumpul.

    Baris dicatat di ``current_line`` lebih dulu dan baru dimasukkan ke ``lines`` pada iterasi berikutnya
    (atau setelah loop) — itulah yang membuat event penghenti tidak ikut.
    """
    lines = []
    current_line = ""
    current_position = None

    for event in events:
        pos, event_data = split_event_line(event)
        event_name, _value = parse_event_data(event_data)
        pos = int(pos)

        if current_position == position:
            lines.append(current_line)

        if pos == position:
            current_position = pos
            current_line = event
        elif event_name == "phrase_start" or event_name == "phrase_end":
            current_position = None

        if current_position is not None and pos != position:
            current_line = event

    if current_position == position:
        lines.append(current_line)

    return lines


def get_lyric_item(events: list[str]) -> list[str]:
    """Teks (value) setiap event phrase SETELAH baris pertama (``phrase_start``), tanpa ``section``.

    Contoh: ``['Hold', 'the', '<color=#FF5E9C>light</color>']``.
    """
    lines_temp = []
    for line in events[1:]:
        pos, event_data = split_event_line(line)
        event_name, value = parse_event_data(event_data)
        if event_name != "section":
            lines_temp.append(value)
    return lines_temp


def extract_phrase_start(lines: list[str]) -> tuple[str | None, list[str]]:
    """``(baris_pertama, sisanya)`` bila baris pertama adalah ``phrase_start``; selain itu ``(None, lines)``."""
    phrase_start = None
    remaining_lines = []

    if lines:
        if lines[0].endswith('phrase_start"'):
            phrase_start = lines[0]
            remaining_lines = lines[1:]
        else:
            return None, lines

    return phrase_start, remaining_lines


def require_phrase_start(lines: list[str]) -> None:
    """Posisi yang dipilih harus berupa awal phrase: baris pertama phrase harus ``phrase_start``."""
    temp_ps, _remaining = extract_phrase_start(lines)
    if temp_ps is None:
        raise JutsuError(MSG_NOT_PHRASE_START)


def split_lyric(lyric: str) -> tuple[int, str]:
    """``'768 = E "lyric Hold"'`` → ``(768, 'Hold')``. Melempar IndexError / ValueError bila bentuknya tidak cocok."""
    parts = lyric.split(' = E "lyric ')
    position = int(parts[0])
    lyric_value = parts[1].strip('"')
    return position, lyric_value


# ─────────────────────────────────────────────────────────────────────────────
#  Menyisipkan & mengurutkan
# ─────────────────────────────────────────────────────────────────────────────
def sort_script_by_position(script: list[str]) -> list[str]:
    """Urutkan menurut posisi di awal baris (stabil: posisi sama → urutan semula)."""
    return sorted(script, key=line_position)


def insert_and_sort(script: list[str], element: list[str] | str) -> list[str]:
    """``script`` + ``element`` (list atau satu baris), lalu diurutkan menurut posisi.

    Karena pengurutannya stabil, untuk posisi yang sama baris ``script`` tampil lebih dulu dari ``element``.
    ``script`` yang diberikan tidak diubah.
    """
    combined = list(script)
    if isinstance(element, list):
        combined.extend(element)
    elif isinstance(element, str):
        combined.append(element)
    return sort_script_by_position(combined)


# ─────────────────────────────────────────────────────────────────────────────
#  Langkah awal yang sama di semua Jutsu berbasis phrase
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class PhraseSelection:
    """Hasil memilah script untuk satu phrase.

    temp_section: semua baris ``section`` di seluruh script (ditambahkan kembali di akhir).
    temp_value:   semua baris lain DI LUAR phrase target, tanpa ``section``.
    lines:        baris phrase target tanpa ``section``; ``lines[0]`` harus ``phrase_start``.
    """

    temp_section: list[str]
    temp_value: list[str]
    lines: list[str]


def select_phrase(script: list[str], position: int) -> PhraseSelection:
    """Langkah awal ``mainLCJutsu`` / ``mainCCjutsu`` / ``mainCnvrtJutsu`` yang lama (urutannya sama)."""
    if not check_position_in_script(script, position):
        raise JutsuError(MSG_POSITION_NOT_FOUND)
    validate_events(script)

    temp_section = get_section_lines(script)
    temp_value = remove_section_lines(script)

    lines = get_lines(script, position)
    temp_value = remove_elements(temp_value, lines)
    lines = remove_section_lines(lines)

    return PhraseSelection(temp_section=temp_section, temp_value=temp_value, lines=lines)
