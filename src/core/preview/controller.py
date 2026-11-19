"""PreviewController — state machine playback + pemetaan posisi audio → state lirik.

Murni Python (tanpa GUI). Audio sebenarnya (QMediaPlayer) dipasang lewat antarmuka ``AudioBackend``
(spesifikasi 12.2), sehingga logika Play/Pause/Stop/Seek/ganti-chart bisa diuji tanpa Qt.

Prinsip (spesifikasi 12.4): **posisi audio dari backend adalah satu-satunya sumber waktu**.
Controller tidak pernah menghitung waktu sendiri dari timer; ``lyric_state()`` selalu dibaca
dari ``backend.position_ms()`` saat dipanggil.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable

from core.preview.scheduler import LyricState
from core.preview.session import PreviewSession
from core.preview.transition import Scene


# Pilihan kecepatan playback untuk dropdown Speed (1.0 = normal).
SPEED_OPTIONS: tuple[float, ...] = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
DEFAULT_SPEED = 1.0
_MIN_SPEED, _MAX_SPEED = 0.25, 4.0           # batas pengaman untuk pemanggil di luar dropdown


def format_speed(rate: float) -> str:
    """``0.5x``, ``0.75x``, ``1x``, ``1.25x``, ``1.5x``, ``2x``."""
    return f"{rate:g}x"


class PlaybackState(str, Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


@runtime_checkable
class AudioBackend(Protocol):
    """Kontrak minimum backend audio. Satuan waktu: milidetik (int).

    ``set_volume(0.0–1.0)`` dan ``set_playback_rate(rate)`` bersifat OPSIONAL: backend yang
    mendukungnya (mis. ``QtAudioBackend``) menambahkannya, ``NullAudioBackend`` mengabaikannya.
    ``position_ms()`` HARUS tetap berupa posisi MEDIA (bukan waktu dinding), sehingga lirik
    otomatis ikut melambat/mempercepat saat ``playback_rate`` berubah.
    """

    is_available: bool

    def load(self, path: Path) -> None: ...
    def unload(self) -> None: ...
    def play(self) -> None: ...
    def pause(self) -> None: ...
    def stop(self) -> None: ...          # berhenti + posisi kembali ke 0
    def position_ms(self) -> int: ...
    def seek(self, position_ms: int) -> None: ...
    def duration_ms(self) -> int: ...    # 0 selagi belum diketahui
    def dispose(self) -> None: ...


class NullAudioBackend:
    """Pengganti saat tidak ada backend audio (mis. QtMultimedia tidak tersedia). Semua no-op."""

    is_available = False

    def load(self, path: Path) -> None: pass
    def unload(self) -> None: pass
    def play(self) -> None: pass
    def pause(self) -> None: pass
    def stop(self) -> None: pass
    def position_ms(self) -> int: return 0
    def seek(self, position_ms: int) -> None: pass
    def duration_ms(self) -> int: return 0
    def set_volume(self, volume: float) -> None: pass       # opsional: tidak ada suara
    def set_playback_rate(self, rate: float) -> None: pass  # opsional: tidak ada suara
    def dispose(self) -> None: pass


def format_time(ms: int | float) -> str:
    """``mm:ss.mmm`` (menit boleh > 59). Nilai negatif/NaN dianggap 0."""
    try:
        total = int(ms)
    except (TypeError, ValueError, OverflowError):
        total = 0
    total = max(0, total)
    minutes, rest = divmod(total, 60_000)
    return f"{minutes:02d}:{rest // 1000:02d}.{rest % 1000:03d}"


class PreviewController:
    def __init__(self, backend: AudioBackend | None = None) -> None:
        self.backend: AudioBackend = backend if backend is not None else NullAudioBackend()
        self.session: PreviewSession | None = None
        self.state = PlaybackState.STOPPED
        self.audio_error: str | None = None          # kegagalan memuat/memutar file yang SUDAH ditemukan
        self.generation = 0                          # naik tiap audio dimuat ulang / dilepas
        self._loaded_path: Path | None = None
        self._at_end = False                         # media selesai secara alami
        self._volume = 1.0                           # 0.0–1.0, diingat walau backend belum punya audio
        self._speed = DEFAULT_SPEED                  # kecepatan playback, diingat walau belum ada audio
        # Audio pilihan pengguna (sementara, hanya di memori). Berlaku selama chart yang sama
        # terbuka; TIDAK pernah ditulis ke chart/MusicStream.
        self._manual_audio: Path | None = None
        self._manual_chart_key: str | None = None    # chart_path saat audio manual dipilih

    # ── status ───────────────────────────────────────────────────────────
    @property
    def loaded_audio(self) -> Path | None:
        return self._loaded_path

    @property
    def manual_audio(self) -> Path | None:
        """File audio sementara pilihan pengguna, atau ``None`` bila memakai audio chart."""
        return self._manual_audio

    @property
    def can_play(self) -> bool:
        return self.backend.is_available and self._loaded_path is not None and self.audio_error is None

    @property
    def notice(self) -> str:
        """Satu pesan status untuk pengguna ('' = siap). Kegagalan backend didahulukan."""
        if self.session is None:
            return "No chart loaded."
        if self._loaded_path is not None and not self.backend.is_available:
            return "Audio player is not available on this system."
        if self.audio_error:
            return self.audio_error
        notices = self.session.notices
        if self._manual_audio is not None:
            # Pesan "audio tidak ditemukan" dari sesi tidak relevan lagi; sisanya (mis. tanpa lirik) tetap.
            rest = notices[1:] if not self.session.audio.ok else notices
            info = f"Temporary Audio: {self._manual_audio.name}."
            return " ".join((info, *rest[:1]))
        return notices[0] if notices else ""

    # ── sesi ─────────────────────────────────────────────────────────────
    def apply_session(self, session: PreviewSession) -> bool:
        """Pasang sesi baru (chart dibuka / teks diedit / file disimpan).

        Bila file audio-nya sama dengan yang sedang dimuat, playback TIDAK terganggu (mengedit lirik
        saat musik berjalan tetap mulus). Bila berbeda, audio lama dilepas dan state kembali STOPPED.
        Mengembalikan True bila audio dimuat ulang/dilepas.
        """
        self.session = session
        if self._manual_audio is not None and session.chart_path != self._manual_chart_key:
            self._manual_audio = None                # chart lain dibuka → audio sementara dilepas
            self._manual_chart_key = None
        new_path = self._effective_audio_path()
        if new_path == self._loaded_path:
            return False
        self._switch_audio(new_path)
        return True

    def _effective_audio_path(self) -> Path | None:
        """Audio manual (bila ada) lebih diutamakan daripada audio hasil resolve chart."""
        if self._manual_audio is not None:
            return self._manual_audio
        if self.session is not None and self.session.audio.ok:
            return self.session.audio.path
        return None

    def _switch_audio(self, new_path: Path | None) -> None:
        self._release_audio()
        self._loaded_path = new_path
        self.generation += 1
        if new_path is not None and self.backend.is_available:
            self.backend.load(new_path)
            self._apply_volume()                     # output audio baru memakai volume yang sudah dipilih
            self._apply_speed()                      # ...dan kecepatan yang sudah dipilih

    # ── audio manual (sementara) ─────────────────────────────────────────
    def load_manual_audio(self, path: str | Path) -> bool:
        """Pakai *path* sebagai audio chart yang sedang terbuka, hanya selama sesi aplikasi ini.

        Tidak mengubah file chart, ``MusicStream``, maupun file audio. Mengembalikan False bila
        belum ada chart atau file tidak ada. Format yang tidak didukung dilaporkan backend
        lewat ``notify_audio_error``.
        """
        if self.session is None:
            return False
        candidate = Path(path)
        try:
            if not candidate.is_file():
                return False
        except (OSError, ValueError):
            return False
        self._manual_audio = candidate
        self._manual_chart_key = self.session.chart_path
        if candidate != self._loaded_path:
            self._switch_audio(candidate)
        return True

    def clear_manual_audio(self) -> bool:
        """Lepas audio sementara dan kembali ke audio chart (bila ada). True bila ada yang dilepas."""
        if self._manual_audio is None:
            return False
        self._manual_audio = None
        self._manual_chart_key = None
        new_path = self._effective_audio_path()
        if new_path != self._loaded_path:
            self._switch_audio(new_path)
        return True

    def _release_audio(self) -> None:
        self.backend.stop()
        self.backend.unload()
        self.state = PlaybackState.STOPPED
        self.audio_error = None
        self._at_end = False
        self._loaded_path = None

    # ── transport ────────────────────────────────────────────────────────
    def play(self) -> bool:
        if not self.can_play:
            return False
        if self._at_end:                              # sudah habis → mulai dari awal
            self.backend.seek(0)
            self._at_end = False
        self.backend.play()
        self.state = PlaybackState.PLAYING
        return True

    def pause(self) -> None:
        if self.state is PlaybackState.PLAYING:
            self.backend.pause()
            self.state = PlaybackState.PAUSED

    def toggle(self) -> bool:
        """Play ↔ Pause. Mengembalikan True bila setelahnya sedang PLAYING."""
        if self.state is PlaybackState.PLAYING:
            self.pause()
            return False
        return self.play()

    def stop(self) -> None:
        """Berhenti dan kembali ke awal chart (spesifikasi 14.3)."""
        if self._loaded_path is not None:
            self.backend.stop()
        self.state = PlaybackState.STOPPED
        self._at_end = False

    def seek_ms(self, position_ms: int) -> int:
        """Lompat ke *position_ms* (di-clamp ke durasi bila diketahui). Mengembalikan posisi efektif."""
        target = max(0, int(position_ms))
        duration = self.backend.duration_ms()
        if duration > 0:
            target = min(target, duration)
        if self._loaded_path is not None:
            self.backend.seek(target)
        self._at_end = False
        return target

    # ── volume ───────────────────────────────────────────────────────────
    @property
    def volume_percent(self) -> int:
        """Volume aktif 0–100."""
        return round(self._volume * 100)

    def set_volume(self, percent: float) -> None:
        """Atur volume 0–100 (di-clamp). Diteruskan ke backend yang punya ``set_volume``."""
        self._volume = max(0.0, min(1.0, float(percent) / 100.0))
        self._apply_volume()

    def _apply_volume(self) -> None:
        setter = getattr(self.backend, "set_volume", None)   # opsional pada kontrak AudioBackend
        if callable(setter):
            setter(self._volume)

    # ── kecepatan ────────────────────────────────────────────────────────
    @property
    def speed(self) -> float:
        """Kecepatan playback aktif (1.0 = normal)."""
        return self._speed

    def set_speed(self, rate: float) -> None:
        """Atur kecepatan playback (di-clamp). Lirik ikut berubah karena clock-nya posisi audio."""
        self._speed = max(_MIN_SPEED, min(_MAX_SPEED, float(rate)))
        self._apply_speed()

    def _apply_speed(self) -> None:
        setter = getattr(self.backend, "set_playback_rate", None)   # opsional pada kontrak AudioBackend
        if callable(setter):
            setter(self._speed)

    # ── dari backend ─────────────────────────────────────────────────────
    def notify_media_ended(self) -> None:
        """Audio habis sendiri. Layar tetap di keadaan terakhir; Play berikutnya mulai dari awal."""
        self.state = PlaybackState.STOPPED
        self._at_end = True

    def notify_audio_error(self, message: str) -> None:
        self.audio_error = message or "Failed to load or play the audio file."
        self.state = PlaybackState.STOPPED
        self._at_end = False

    # ── clock ────────────────────────────────────────────────────────────
    def position_ms(self) -> int:
        if self._loaded_path is None:
            return 0
        return max(0, int(self.backend.position_ms()))

    def duration_ms(self) -> int:
        return max(0, int(self.backend.duration_ms())) if self._loaded_path is not None else 0

    def lyric_state(self) -> LyricState | None:
        """State lirik pada posisi audio SAAT INI (None bila belum ada sesi)."""
        if self.session is None:
            return None
        return self.session.scheduler.state_at_audio(self.position_ms() / 1000.0)

    def scene(self) -> Scene | None:
        """Adegan (phrase sekarang/berikutnya + transisi) pada posisi audio SAAT INI."""
        if self.session is None:
            return None
        return self.session.timeline.scene_at(self.session.timing.audio_to_chart_seconds(self.position_ms() / 1000.0))

    def scene_at_ms(self, position_ms: int) -> Scene | None:
        """Adegan pada posisi audio tertentu (pratinjau saat slider diseret)."""
        if self.session is None:
            return None
        return self.session.timeline.scene_at(
            self.session.timing.audio_to_chart_seconds(max(0, position_ms) / 1000.0))

    def lyric_state_at_ms(self, position_ms: int) -> LyricState | None:
        """State lirik pada posisi tertentu (untuk pratinjau saat slider diseret)."""
        if self.session is None:
            return None
        return self.session.scheduler.state_at_audio(max(0, position_ms) / 1000.0)

    # ── penutupan ────────────────────────────────────────────────────────
    def dispose(self) -> None:
        self._release_audio()
        self.backend.dispose()
        self.session = None
