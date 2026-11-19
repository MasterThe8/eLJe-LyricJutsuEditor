"""Adapter ``QMediaPlayer`` untuk ``core.preview.controller.AudioBackend``.

Satu-satunya modul yang mengimpor ``QtMultimedia``. Proyek belum punya backend audio sebelum
fitur ini, jadi ini bukan duplikasi; pemiliknya adalah jendela Live Preview dan dilepas bersamanya.

Catatan teknis:

* ``QMediaPlayer`` memuat sumber secara asinkron. Kegagalan (file rusak, codec tidak ada) datang
  lewat sinyal ``error_occurred``, bukan exception dari ``load()``.
* ``playbackRate`` mengubah laju ``position()`` (posisi MEDIA), jadi clock lirik otomatis ikut.
  Backend mengingat rate-nya dan memasangnya ulang setelah media selesai dimuat, karena sebagian
  backend multimedia mengabaikan rate yang diset sebelum media siap.
* ``position()`` QMediaPlayer di sebagian platform hanya diperbarui tiap puluhan milidetik.
  Backend ini meneruskannya apa adanya; penghalusan clock (bila perlu) bukan tugas backend ini.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal

try:
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
except ImportError:                                  # modul multimedia tidak terpasang
    QAudioOutput = None                              # type: ignore[assignment]
    QMediaPlayer = None                              # type: ignore[assignment]


class QtAudioBackend(QObject):
    """Implementasi ``AudioBackend`` di atas QMediaPlayer + QAudioOutput."""

    is_available = True

    error_occurred = Signal(str)       # pesan kegagalan memuat/memutar
    duration_changed = Signal(int)     # ms
    media_ended = Signal()             # audio habis secara alami

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._disposed = False
        self._rate = 1.0
        self._player = QMediaPlayer(self)
        self._output = QAudioOutput(self)
        self._player.setAudioOutput(self._output)
        self._player.errorOccurred.connect(self._on_error)
        self._player.durationChanged.connect(self._on_duration)
        self._player.mediaStatusChanged.connect(self._on_status)

    # ── AudioBackend ─────────────────────────────────────────────────────
    def load(self, path: Path) -> None:
        self._player.setSource(QUrl.fromLocalFile(str(path)))      # aman untuk nama Unicode/spasi

    def unload(self) -> None:
        self._player.setSource(QUrl())

    def play(self) -> None:
        self._player.play()

    def pause(self) -> None:
        self._player.pause()

    def stop(self) -> None:
        self._player.stop()

    def position_ms(self) -> int:
        return int(self._player.position())

    def seek(self, position_ms: int) -> None:
        self._player.setPosition(int(position_ms))

    def duration_ms(self) -> int:
        return max(0, int(self._player.duration()))

    def set_volume(self, volume: float) -> None:
        """Atur volume 0.0–1.0 (di-clamp)."""
        self._output.setVolume(max(0.0, min(1.0, float(volume))))

    def set_playback_rate(self, rate: float) -> None:
        """Atur kecepatan playback (1.0 = normal)."""
        self._rate = max(0.1, float(rate))
        self._player.setPlaybackRate(self._rate)

    def dispose(self) -> None:
        """Lepaskan file dan device audio. Aman dipanggil berulang."""
        if self._disposed:
            return
        self._disposed = True
        for signal in (self._player.errorOccurred, self._player.durationChanged,
                       self._player.mediaStatusChanged):
            try:
                signal.disconnect()
            except (RuntimeError, TypeError):
                pass
        self._player.stop()
        self._player.setSource(QUrl())
        try:
            self._player.setAudioOutput(None)
        except TypeError:                              # binding yang menolak None
            pass
        self._player.deleteLater()
        self._output.deleteLater()
        self.deleteLater()

    # ── slot internal ────────────────────────────────────────────────────
    def _on_error(self, _error, message: str = "") -> None:
        self.error_occurred.emit(message or "Failed to load or play the audio file.")

    def _on_duration(self, duration: int) -> None:
        self.duration_changed.emit(max(0, int(duration)))

    def _on_status(self, status) -> None:
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            if abs(self._player.playbackRate() - self._rate) > 1e-6:
                self._player.setPlaybackRate(self._rate)     # media baru: pasang ulang rate pilihan
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.media_ended.emit()


def create_audio_backend(parent: QObject | None = None) -> QtAudioBackend | None:
    """Buat backend, atau ``None`` bila QtMultimedia tidak tersedia / gagal diinisialisasi."""
    if QMediaPlayer is None or QAudioOutput is None:
        return None
    try:
        return QtAudioBackend(parent)
    except Exception:                                # noqa: BLE001 — mis. tidak ada device audio
        return None
