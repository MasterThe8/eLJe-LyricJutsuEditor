"""Chart Audio Resolver — menentukan file audio milik sebuah chart dari ``[Song] MusicStream``.

Murni Python (tanpa GUI, tanpa audio backend). Tugasnya hanya *menemukan* file; memuat/memutarnya
adalah urusan audio backend.

Aturan:

* Nama file selalu berasal dari ``MusicStream`` — tidak ada nama yang di-hardcode (``song.ogg``
  dll.) dan tidak pernah memilih file audio lain secara otomatis.
* Path di-resolve **relatif terhadap folder chart**. Path absolut, drive Windows (``C:\\...``),
  UNC, dan komponen ``..`` ditolak (``INVALID_PATH``) supaya chart tidak bisa mengarahkan preview
  ke file di luar folder lagunya.
* ``\\`` dianggap pemisah folder, karena banyak chart ditulis di Windows.
* Nama Unicode dipertahankan apa adanya. Bila file tidak ditemukan persis, bentuk normalisasi
  NFC/NFD dicoba (nama file di macOS tersimpan NFD, sedangkan teks chart biasanya NFC).
* Format audio **tidak** dibatasi di sini kecuali pemanggil memberi ``supported_extensions`` (daftar dari backend);
  bila diberi, file dengan ekstensi lain dilaporkan ``UNSUPPORTED_FORMAT``.
* Fungsi ini tidak pernah melempar exception untuk input buruk; hasilnya selalu ``AudioResolution``.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Collection
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from core.preview.chart_info import read_chart_info


class AudioStatus(str, Enum):
    OK = "ok"
    NO_CHART_PATH = "no_chart_path"                  # chart belum punya lokasi file (belum disimpan)
    MISSING_MUSIC_STREAM = "missing_music_stream"    # [Song] tanpa MusicStream / kosong / None
    INVALID_PATH = "invalid_path"                    # absolut / keluar folder chart / karakter ilegal
    NOT_FOUND = "not_found"                          # path valid, tetapi file tidak ada
    UNSUPPORTED_FORMAT = "unsupported_format"        # ekstensi tidak ada di supported_extensions


@dataclass(frozen=True)
class AudioResolution:
    """Hasil resolusi audio. ``path`` hanya terisi bila ``status == OK``."""

    status: AudioStatus
    path: Path | None
    music_stream: str | None
    message: str

    @property
    def ok(self) -> bool:
        return self.status is AudioStatus.OK


_DRIVE_RE = re.compile(r"^[A-Za-z]:")


def _safe_parts(music_stream: str) -> list[str] | None:
    """Pecah ``MusicStream`` jadi komponen path relatif, atau ``None`` bila tidak aman."""
    if "\x00" in music_stream:
        return None
    normalised = music_stream.replace("\\", "/")
    if normalised.startswith("/") or _DRIVE_RE.match(normalised):      # absolut, UNC (//), drive
        return None
    parts = [p for p in normalised.split("/") if p not in ("", ".")]
    if not parts or any(p == ".." for p in parts):
        return None
    return parts


def _is_file(path: Path) -> bool:
    try:
        return path.is_file()
    except (OSError, ValueError):                    # nama terlalu panjang / karakter ilegal di OS ini
        return False


def resolve_chart_audio(
    chart_path: str | Path | None,
    music_stream: str | None,
    *,
    supported_extensions: Collection[str] | None = None,
) -> AudioResolution:
    """Cari file audio untuk chart di *chart_path* berdasarkan nilai ``MusicStream``.

    Args:
        chart_path:  Lokasi file ``.chart`` yang sedang dibuka.
        music_stream: Nilai ``[Song] MusicStream`` (``ChartSongInfo.music_stream``).
        supported_extensions: Ekstensi yang diterima audio backend (mis. ``{".ogg", ".mp3"}``),
            tanpa memperhatikan huruf besar/kecil. ``None`` = tidak memfilter.
    """
    if not chart_path or not str(chart_path).strip():
        return AudioResolution(AudioStatus.NO_CHART_PATH, None, music_stream,
                               "The chart file path is unavailable.")

    if music_stream is None or not music_stream.strip():
        return AudioResolution(AudioStatus.MISSING_MUSIC_STREAM, None, None,
                               "[Song] does not have a MusicStream.")

    parts = _safe_parts(music_stream)
    if parts is None:
        return AudioResolution(
            AudioStatus.INVALID_PATH, None, music_stream,
            f"MusicStream is invalid or outside the chart folder: {music_stream!r}")

    chart_directory = Path(chart_path).expanduser().absolute().parent
    candidates = [parts]
    for form in ("NFC", "NFD"):
        variant = [unicodedata.normalize(form, p) for p in parts]
        if variant not in candidates:
            candidates.append(variant)

    for candidate in candidates:
        audio_path = chart_directory.joinpath(*candidate)
        if not _is_file(audio_path):
            continue
        if supported_extensions is not None:
            allowed = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in supported_extensions}
            if audio_path.suffix.lower() not in allowed:
                return AudioResolution(
                    AudioStatus.UNSUPPORTED_FORMAT, None, music_stream,
                    f"Audio format is not supported: {audio_path.suffix or '(no extension)'}")
        return AudioResolution(AudioStatus.OK, audio_path, music_stream, f"Audio: {audio_path.name}")

    return AudioResolution(
        AudioStatus.NOT_FOUND, None, music_stream,
        f"Audio file '{music_stream}' not found in the chart folder.")


def resolve_audio_for_chart(doc, chart_path: str | Path | None = None, *,
                            supported_extensions: Collection[str] | None = None) -> AudioResolution:
    """Pintasan: baca ``MusicStream`` dari ``ChartDocument`` lalu resolve.

    *chart_path* default ke ``doc.file_path``. Catatan integrasi: ``ChartDocument.file_path`` tidak
    diperbarui oleh "Save As", jadi MainWindow sebaiknya memberi path yang sedang aktif.
    """
    info = read_chart_info(doc)
    return resolve_chart_audio(
        chart_path if chart_path is not None else getattr(doc, "file_path", None),
        info.song.music_stream,
        supported_extensions=supported_extensions,
    )
