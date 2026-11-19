"""Nilai bawaan aplikasi ("Set Default"), satu sumber untuk dialog setting dan jendela utama.
Nilai awal DEFAULTS diambil dari setting.ini asli.
"""
from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
#  Nilai bawaan ("Set Default") — sumber tunggal untuk dialog setting dan jendela utama
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_HIGHLIGHT = {
    "position": "#FF00FF",
    "value": "#F5FF5E",
    "richtag": "#00FF7F",
    "eventname": "#03FCF4",
}
# Warna awal Color Picker. Sengaja konstanta, BUKAN Theme.ACCENT: ini warna lirik milik pengguna
# dan tidak boleh ikut berubah saat tema aplikasi diganti.
DEFAULT_PICKER_COLOR = "#1BEEF5"
DEFAULT_LYRIC = {"closing_lyric": "-", "hidden_lyric": "_"}
DEFAULT_SHORTCUTS = {
    "jutsueditor": "Alt+J", "livepreview": "Alt+L",
    "toggle_display": "Alt+D", "toggle_treeview": "Alt+Q", "toggle_temptext": "Alt+E",
    "colorpicker": "Alt+A", "getsymbol": "Alt+S", "weirdtext": "Alt+W",
    "addjutsu": "Alt+1", "batchjutsu": "Alt+2",
    "colorjutsu1": "Alt+3", "colorjutsu2": "Alt+4", "kan2romjutsu": "Alt+5",
    "b_tag": "Ctrl+B", "i_tag": "Ctrl+I", "color_tag": "Ctrl+L", "br_tag": "Ctrl+K",
    "voffset_tag": "Ctrl+J", "smallcaps_tag": "Ctrl+/", "lowercase_tag": "Ctrl+,",
    "uppercase_tag": "Ctrl+.", "mspace_tag": "Ctrl+M", "cspace_tag": "Ctrl+N",
    "sub_tag": "Ctrl+;", "sup_tag": "Ctrl+'",
}


# ─────────────────────────────────────────────────────────────────────────────
#  Konfigurasi bawaan (nilai diambil dari setting.ini asli)
#  Hanya nilai AWAL: nilai yang dipakai aplikasi ada di services.settings (bawaan + yang tersimpan pengguna).
# ─────────────────────────────────────────────────────────────────────────────
DEFAULTS = {
    "chart_dir": "",       # fallback ke home bila tidak ada
    "display": True,       # live preview tab "Display Lyrics/RichText Lyrics"
    "treeview": True,      # dock direktori
    "temptext": True,      # dock TempText + Symbol Picker (ini aslinya False)
    "editor_font_size": 13,
}

# Font editor. ``family`` kosong = font bawaan editor itu (monospace untuk PlainText, font aplikasi untuk Display).
DEFAULT_FONT_PLAIN = {"family": "", "size": DEFAULTS["editor_font_size"], "bold": False, "italic": False}
DEFAULT_FONT_RICH = {"family": "", "size": 18, "bold": False, "italic": False}
# Panel yang tampil (menu View / tombol toolbar kanan).
DEFAULT_VIEW = {key: DEFAULTS[key] for key in ("display", "treeview", "temptext")}

SAMPLE_EVENTS = """\
0 = E "section Intro"
768 = E "phrase_start"
768 = E "lyric Hold"
864 = E "lyric the"
960 = E "lyric <color=#FF5E9C>light</color>"
1152 = E "phrase_end"
1536 = E "phrase_start"
1536 = E "lyric Where"
1632 = E "lyric the"
1728 = E "lyric dark-"
1824 = E "lyric <i>ness</i>"
1920 = E "lyric fades"
2304 = E "phrase_end"
3072 = E "section Verse 1"
3072 = E "phrase_start"
3072 = E "lyric <b>Count</b>"
3168 = E "lyric ev-"
3264 = E "lyric ery"
3360 = E "lyric star"
3552 = E "phrase_end"
3840 = E "phrase_start"
3840 = E "lyric Un-"
3936 = E "lyric til"
4032 = E "lyric the"
4128 = E "lyric <color=#1BEEF5>dawn</color>"
4608 = E "phrase_end"
"""
