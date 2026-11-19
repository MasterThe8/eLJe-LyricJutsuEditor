"""Writer file .chart — menyimpan ChartDocument ke disk.

Logika dimigrasi dari:
  - ``main.py`` method ``save_file()`` (baris 1125-1161)

Perbaikan dibanding kode asli:
  - Tidak terikat pada GUI (QFileDialog, QMessageBox).
  - Encoding asli file dipakai lagi secara default; BOM ikut dipertahankan.
  - Hanya body ``[Events]`` yang diganti, section lain disalin dari file asli.
  - Jika karakter baru tidak bisa di-encode dengan encoding asli, writer
    fallback ke UTF-8 dan melaporkannya lewat ``WriteResult``.
"""
from __future__ import annotations

import codecs
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from core.chart.document import ChartDocument
from core.chart.encoding import encode_text, normalise_codec, pretty_name


@dataclass(frozen=True)
class WriteResult:
    """Informasi hasil penyimpanan file."""

    encoding: str
    bom: bytes = b""
    fallback: bool = False
    warning: str | None = None


def write_chart_file(
    doc: ChartDocument,
    path: Union[str, Path],
    editor_text: str,
    *,
    encoding: str | None = None,
) -> WriteResult:
    """Tulis file .chart ke *path*.

    Args:
        doc:         ChartDocument yang menyimpan section-section non-event.
        path:        Path tujuan penyimpanan.
        editor_text: Isi editor PlainText (events body yang sudah diedit user).
        encoding:    Paksa encoding output. Jika ``None`` (default), encoding
                     asli file dipakai kembali.

    Raises:
        OSError: Jika gagal menulis file (permission, disk penuh, dll).
        UnicodeEncodeError: Jika *encoding* dipaksa eksplisit tapi tidak bisa
            merepresentasikan teks baru.
        ValueError: Jika nama encoding tidak dikenal.
    """
    path = Path(path)
    assembled = doc.assembled_text(editor_text)

    explicit_encoding = encoding is not None
    target_encoding = encoding or doc.encoding or "utf-8"
    codec = normalise_codec(target_encoding)
    if codec is None:
        raise ValueError(f"Unknown encoding: {target_encoding!r}")

    # BOM hanya dipertahankan bila encoding target masih satu keluarga.
    original_codec = normalise_codec(doc.encoding)
    bom = doc.bom if codec == original_codec else b""

    fallback = False
    warning = None

    try:
        data = encode_text(assembled, encoding=codec, bom=bom)
    except UnicodeEncodeError:
        if explicit_encoding:
            raise

        # Karakter baru (mis. huruf Jepang) tidak muat di encoding lama.
        # Tulis ulang seluruh file sebagai UTF-8 agar tetap valid.
        fallback = True
        original_label = pretty_name(original_codec or doc.encoding)
        target_encoding = "utf-8"
        codec = "utf-8"
        bom = codecs.BOM_UTF8 if doc.bom == codecs.BOM_UTF8 else b""
        data = encode_text(assembled, encoding=codec, bom=bom)
        warning = (
            f"The original file was {original_label}, but the new text contains "
            "characters that encoding cannot represent. The file was saved as "
            "UTF-8."
        )

    path.write_bytes(data)

    # Update state dokumen agar save berikutnya konsisten.
    doc.file_path = str(path)
    doc.encoding = codec
    doc.bom = bom

    return WriteResult(
        encoding=codec,
        bom=bom,
        fallback=fallback,
        warning=warning,
    )


def assemble_chart_text(doc: ChartDocument, editor_text: str) -> str:
    """Gabungkan semua section menjadi teks .chart utuh tanpa menulis ke disk.

    Berguna untuk preview atau validasi sebelum save.
    """
    return doc.assembled_text(editor_text)
