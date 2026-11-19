"""Definisi tag rich-text lirik yang bisa disisipkan lewat shortcut (Ctrl+B, Ctrl+I, …)."""
from __future__ import annotations

# (nama shortcut, tag, atribut bawaan, tag penutup?)  — dipakai insert tag
TAG_SHORTCUTS = [
    ("b_tag", "b", ""), ("i_tag", "i", ""), ("color_tag", "color", "=#"),
    ("br_tag", "br", None), ("voffset_tag", "voffset", "=0"),
    ("smallcaps_tag", "smallcaps", ""), ("lowercase_tag", "lowercase", ""),
    ("uppercase_tag", "uppercase", ""), ("mspace_tag", "mspace", "=0"),
    ("cspace_tag", "cspace", "=0"), ("sub_tag", "sub", ""), ("sup_tag", "sup", ""),
]
