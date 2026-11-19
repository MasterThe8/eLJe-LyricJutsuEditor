"""Pembangun event untuk Lyric Color (method 2) dan Kan2Rom — keduanya memakai logika yang sama.

Asal: ``cc_hide`` / ``cc_nohide`` / ``cc_addnext`` / ``add_next_lyric`` di CCJutsu.py dan CnvrtJutsu.py.
(Di file lama keduanya salinan; perbedaan antar salinan hanya baris kosong.)

Cara kerjanya
-------------
Setiap baris phrase (TERMASUK ``phrase_start`` di baris pertama) diubah menjadi satu "grup" event:

    cc_hide     5 baris:  pos     lyric <closing>
                          pos+1   phrase_start
                          pos+2   lyric <hidden>
                          pos+3   phrase_start
                          pos+4   lyric <color=HEX>...teks yang sudah diwarnai...</color>
    cc_nohide   3 baris:  pos, pos+1, pos+2  (tanpa baris tengah)
    cc_addnext  5 baris:  seperti cc_hide, tetapi baris tengahnya memakai teks "next lyric" dari pengguna

``phrase_start`` bernilai kosong, jadi ia menghasilkan grup berisi warna kosong dan menambahkan satu spasi ke
``previous_lyric``. Spasi itulah yang dibuang oleh ``replace("> ", ">")`` di akhir (lihat ``assemble_color_script``).

Lalu ``add_next_lyric`` menempelkan sisa lirik berwarna putih (#FFFFFF) di belakang tiap teks berwarna.
"""
from __future__ import annotations

from core.operations.errors import JutsuError
from core.operations.script import (
    PhraseSelection,
    insert_and_sort,
    lyric_event,
    parse_event_data,
    phrase_start_event,
    sort_script_by_position,
    split_event_line,
)

DEFAULT_COLOR = "#fca101"
WHITE = "#FFFFFF"

# Pilihan "Next phrase" di dialog (harus sama dengan ColorJutsuDialog.OPTIONS)
NEXT_PHRASE_HIDE = "Default (Hide Next Phrase)"
NEXT_PHRASE_SHOW = "Show Next Phrase"
NEXT_PHRASE_ADD = "Add Next Lyric"


def normalize_color(color: str | None) -> str:
    """Hex warna untuk tag ``<color=...>``. Huruf kecil, seperti ``QColor.name()`` di aplikasi lama (#fca101)."""
    if not color:
        return DEFAULT_COLOR
    return str(color).lower()


def _close_last_group(result: list[str]) -> list[str]:
    """Grup terakhir: buang spasi sebelum ``</color>`` penutup."""
    last_line = result[-1]
    last_line = last_line.replace(" </color>", "</color>")
    result[-1] = last_line
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  Default (Hide Next Phrase)
# ─────────────────────────────────────────────────────────────────────────────
def cc_hide(lines: list[str], color: str | None, closing_lyric: str, hidden_lyric: str) -> list[str]:
    """Grup 5 baris, baris tengah = ``hidden_lyric``. Urutan grup = urutan ``lines`` (tidak di-sort)."""
    result = []
    previous_lyric = ""
    hex_value = normalize_color(color)

    for line in lines:
        pos, event_data = split_event_line(line)
        _event_name, value = parse_event_data(event_data)
        lyric = value.replace("-", "")                     # semua '-' dibuang

        if "-" in value:                                   # suku kata bersambung → tanpa spasi
            line1 = lyric_event(int(pos), closing_lyric)
            line2 = phrase_start_event(int(pos) + 1)
            line3 = lyric_event(int(pos) + 2, hidden_lyric)
            line4 = phrase_start_event(int(pos) + 3)
            line5 = lyric_event(int(pos) + 4, "<color=" + hex_value + ">" + previous_lyric + lyric + "</color>")
            line = line1 + "\n" + line2 + "\n" + line3 + "\n" + line4 + "\n" + line5
            previous_lyric += lyric
        else:                                              # kata utuh → diikuti spasi
            line1 = lyric_event(int(pos), closing_lyric)
            line2 = phrase_start_event(int(pos) + 1)
            line3 = lyric_event(int(pos) + 2, hidden_lyric)
            line4 = phrase_start_event(int(pos) + 3)
            line5 = lyric_event(int(pos) + 4, "<color=" + hex_value + ">" + previous_lyric + lyric + " " + "</color>")
            line = line1 + "\n" + line2 + "\n" + line3 + "\n" + line4 + "\n" + line5
            previous_lyric += lyric + " "

        result.append(line)

    return _close_last_group(result)


# ─────────────────────────────────────────────────────────────────────────────
#  Show Next Phrase
# ─────────────────────────────────────────────────────────────────────────────
def cc_nohide(lines: list[str], color: str | None, closing_lyric: str) -> list[str]:
    """Grup 3 baris (tanpa baris tengah). Grup DI-SORT menurut posisi sebelum grup terakhir dirapikan."""
    result = []
    previous_lyric = ""
    hex_value = normalize_color(color)

    for line in lines:
        pos, event_data = split_event_line(line)
        _event_name, value = parse_event_data(event_data)
        lyric = value.replace("-", "")

        if "-" in value:
            line1 = lyric_event(int(pos), closing_lyric)
            line2 = phrase_start_event(int(pos) + 1)
            line3 = lyric_event(int(pos) + 2, "<color=" + hex_value + ">" + previous_lyric + lyric + "</color>")
            line = line1 + "\n" + line2 + "\n" + line3
            previous_lyric += lyric
        else:
            line1 = lyric_event(int(pos), closing_lyric)
            line2 = phrase_start_event(int(pos) + 1)
            line3 = lyric_event(int(pos) + 2, "<color=" + hex_value + ">" + previous_lyric + lyric + " " + "</color>")
            line = line1 + "\n" + line2 + "\n" + line3
            previous_lyric += lyric + " "

        result.append(line)

    result = sort_script_by_position(result)
    return _close_last_group(result)


# ─────────────────────────────────────────────────────────────────────────────
#  Add Next Lyric
# ─────────────────────────────────────────────────────────────────────────────
def cc_addnext(lines: list[str], color: str | None, closing_lyric: str, next_lyric: str) -> list[str]:
    """Grup 5 baris, baris tengah = ``next_lyric`` dari pengguna. Grup DI-SORT seperti ``cc_nohide``."""
    result = []
    previous_lyric = ""
    hex_value = normalize_color(color)

    for line in lines:
        pos, event_data = split_event_line(line)
        _event_name, value = parse_event_data(event_data)
        lyric = value.replace("-", "")

        if "-" in value:
            line1 = lyric_event(int(pos), closing_lyric)
            line2 = phrase_start_event(int(pos) + 1)
            line3 = lyric_event(int(pos) + 2, next_lyric)
            line4 = phrase_start_event(int(pos) + 3)
            line5 = lyric_event(int(pos) + 4, "<color=" + hex_value + ">" + previous_lyric + lyric + "</color>")
            line = line1 + "\n" + line2 + "\n" + line3 + "\n" + line4 + "\n" + line5
            previous_lyric += lyric
        else:
            line1 = lyric_event(int(pos), closing_lyric)
            line2 = phrase_start_event(int(pos) + 1)
            line3 = lyric_event(int(pos) + 2, next_lyric)
            line4 = phrase_start_event(int(pos) + 3)
            line5 = lyric_event(int(pos) + 4, "<color=" + hex_value + ">" + previous_lyric + lyric + " " + "</color>")
            line = line1 + "\n" + line2 + "\n" + line3 + "\n" + line4 + "\n" + line5
            previous_lyric += lyric + " "

        result.append(line)

    result = sort_script_by_position(result)
    return _close_last_group(result)


def build_color_groups(lines: list[str], option: str, color: str | None, next_lyric: str,
                       closing_lyric: str, hidden_lyric: str) -> list[str]:
    """Pilih pembangun sesuai radio button "Next phrase" di dialog."""
    if option == NEXT_PHRASE_HIDE:
        return cc_hide(lines, color, closing_lyric, hidden_lyric)
    if option == NEXT_PHRASE_SHOW:
        return cc_nohide(lines, color, closing_lyric)
    if option == NEXT_PHRASE_ADD:
        return cc_addnext(lines, color, closing_lyric, next_lyric)
    raise JutsuError(f"Unknown next-phrase option: {option!r}")


# ─────────────────────────────────────────────────────────────────────────────
#  Menempelkan sisa lirik putih
# ─────────────────────────────────────────────────────────────────────────────
def add_next_lyric(lyric_items: list[str], script: list[str]) -> list[str]:
    """Tempelkan sisa lirik (putih) di belakang setiap ``</color>`` hasil ``cc_*``.

    1. Baris-baris ``script`` dimasukkan ke dict ``{posisi: data}``. Dua baris berposisi sama TIDAK
       disimpan dua-duanya: yang terakhir menimpa nilai, urutan tetap urutan kemunculan pertama.
       (Inilah yang membuat grup ``phrase_start`` tertimpa grup lirik pertama bila posisinya sama.)
    2. ``value_to_insert[i]`` = lirik dari item ke-i sampai akhir, dibungkus ``<color=#FFFFFF>...</color>``.
    3. Baris yang memuat ``</color>`` (``color_values``) menerima ``value_to_insert`` sesuai urutannya;
       baris berwarna terakhir tidak menerima apa pun.
    """
    script_temp = {}
    for item in script:
        pos, event_data = split_event_line(item)
        script_temp[int(pos)] = event_data

    temp_lyric = lyric_items.copy()
    value_to_insert = []
    color_values = []

    # Sisa lirik mulai dari tiap item; '- ' (sambungan suku kata) dibuang
    for i in range(len(temp_lyric)):
        temp = " ".join(temp_lyric[i:])
        result = "".join(temp).replace("- ", "")
        if "</color>_" in temp_lyric:                      # perilaku asli: cocok hanya bila ada ITEM persis '</color>_'
            lyric_result = "<color=" + WHITE + "> " + result + "</color>"
        else:
            lyric_result = "<color=" + WHITE + ">" + result + "</color>"
        value_to_insert.append(lyric_result)

    # Ambil baris yang memuat </color>
    for key, value in script_temp.items():
        if "</color>" in value:
            color_values.append(value)

    length_value_to_insert = len(value_to_insert)
    length_color_values = len(color_values)

    # </color>  →  </color> + sisa lirik putih
    for i in range(length_color_values - 1):
        if i < length_value_to_insert:
            color_values[i] = color_values[i].replace("</color>", f"</color>{value_to_insert[i]}")

    # Kembalikan nilai color_values ke dict
    for i, key in enumerate(script_temp):
        if "</color>" in script_temp[key]:
            script_temp[key] = color_values.pop(0)

    return [f"{key} = {value}" for key, value in script_temp.items()]


def assemble_color_script(selection: PhraseSelection, lyric_items: list[str], result: list[str]) -> str:
    """Langkah akhir ``mainCCjutsu`` / ``mainCnvrtJutsu``: tempel sisa lirik, gabungkan semua baris, rapikan spasi.

    Urutan gabung (posisi sama): baris hasil Jutsu → ``section`` → baris lain di luar phrase.
    ``replace("> ", ">")`` berlaku ke SELURUH script, bukan hanya baris hasil Jutsu (perilaku asli).
    """
    result_split = [line for group in result for line in group.split("\n")]
    last_result = add_next_lyric(lyric_items, result_split)

    final_result = insert_and_sort(last_result, selection.temp_section)
    final_result = insert_and_sort(final_result, selection.temp_value)
    final_result = "\n".join(final_result)
    final_result = final_result.replace("> ", ">")
    return final_result
