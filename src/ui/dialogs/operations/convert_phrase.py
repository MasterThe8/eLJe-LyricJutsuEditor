"""Dialog Kan2Rom no Jutsu."""
from __future__ import annotations

from ui.dialogs.operations.color_base import ColorJutsuDialog


class Kan2RomDialog(ColorJutsuDialog):
    def __init__(self, parent=None):
        super().__init__("Kan2Rom no Jutsu", "Pair a kanji lyric with its romaji.",
                         "kan2rom", parent, with_options=True, with_kanji=True)
