"""Dialog Lyric Color no Jutsu (method 1 dan 2)."""
from __future__ import annotations

from ui.dialogs.operations.color_base import ColorJutsuDialog


class LyricColorMethod1Dialog(ColorJutsuDialog):
    EVENT_ROWS = 10         # skrip tetap method 1 = 10 baris

    def __init__(self, parent=None):
        super().__init__("Lyric Color no Jutsu (method 1)", "Color a lyric starting at a position.",
                         "lyricolor", parent, with_options=False)


class LyricColorMethod2Dialog(ColorJutsuDialog):
    def __init__(self, parent=None):
        super().__init__("Lyric Color no Jutsu (method 2)", "Color a lyric and decide what happens to the next phrase.",
                         "palette", parent, with_options=True)
