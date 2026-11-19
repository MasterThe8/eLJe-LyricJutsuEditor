"""Pratinjau tab Display Lyrics — menggunakan core.lyrics.renderer."""
from __future__ import annotations

from core.lyrics.renderer import render_lyrics_html
from ui.theme import Theme


def build_preview_html(text: str) -> str:
    """Konversi teks event body menjadi HTML untuk tab Display Lyrics.

    Menggunakan ``render_lyrics_html`` dari ``core.lyrics.renderer``
    untuk pipeline rendering lengkap (parse events → gabung → konversi tag).
    Jika hasil kosong, tampilkan placeholder.
    """
    html = render_lyrics_html(text)
    if not html:
        return (
            f"<p align='center' style='color:{Theme.FAINT}'>"
            f"<br><br>Nothing to display yet</p>"
        )

    # Wrap dalam alignment tengah + spacing antar baris
    # Karena render_lyrics_html mengembalikan satu blok dengan <br>,
    # kita bisa langsung membungkusnya.
    return f"<p align='center' style='margin:0; line-height:2.0'>{html}</p>"
