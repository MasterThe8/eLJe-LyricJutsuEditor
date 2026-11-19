"""Window "eLJe | Live Lyrics Preview" (top-level, terpisah dari central widget MainWindow).

Pembagian tugas:
    PreviewController  → state playback + pemetaan posisi audio → state lirik (core, tanpa Qt)
    QtAudioBackend     → QMediaPlayer (satu-satunya sumber waktu)
    LyricsViewport     → menggambar LyricState
    PlaybackControls   → tombol + slider + label waktu

QTimer di sini HANYA memicu pembacaan ulang posisi audio untuk menggambar; ia bukan sumber waktu
musikal (spesifikasi 12.4). Timer hanya berjalan saat PLAYING; saat pause/stop/seek layar
diperbarui satu kali secara eksplisit.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QFileDialog, QLabel, QMainWindow, QMessageBox, QVBoxLayout, QWidget

from core.preview.controller import PlaybackState, PreviewController
from core.preview.session import PreviewSession
from ui.lyrics_preview.audio_backend import create_audio_backend
from ui.lyrics_preview.controls import PlaybackControls
from ui.lyrics_preview.viewport import LyricsViewport
from ui.theme import bind_icon

WINDOW_TITLE = "eLJe | Live Lyrics Preview"
REFRESH_INTERVAL_MS = 16
AUDIO_FILE_FILTER = ("Audio files (*.ogg *.opus *.mp3 *.wav *.flac *.m4a *.aac *.wma);;"
                     "All files (*)")


class LiveLyricsPreviewWindow(QMainWindow):
    def __init__(self, parent=None, backend=None) -> None:
        """*backend*: ``AudioBackend`` siap pakai (mis. untuk tes). ``None`` = buat QMediaPlayer
        otomatis; bila QtMultimedia tidak ada, controller memakai ``NullAudioBackend``."""
        super().__init__(parent)
        self.setObjectName("liveLyricsPreviewWindow")
        self.setWindowTitle(WINDOW_TITLE)
        bind_icon(self, "setWindowIcon", "live_preview", "ACCENT", "ACCENT")
        self.setMinimumSize(560, 360)
        self.resize(900, 560)
        self._disposed = False
        self._last_key = None

        if backend is None:
            backend = create_audio_backend(self)
        self._controller = PreviewController(backend)

        self.viewport = LyricsViewport()
        self.notice = QLabel()
        self.notice.setObjectName("previewNotice")
        self.notice.setWordWrap(True)
        self.notice.hide()
        self.controls = PlaybackControls()

        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.viewport, 1)
        lay.addWidget(self.notice)
        lay.addWidget(self.controls)
        self.setCentralWidget(central)

        self._timer = QTimer(self)
        self._timer.setInterval(REFRESH_INTERVAL_MS)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._tick)

        self._space = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self._space.setContext(Qt.ShortcutContext.WindowShortcut)
        self._space.activated.connect(self._on_play_toggled)

        self.controls.play_toggled.connect(self._on_play_toggled)
        self.controls.stop_clicked.connect(self._on_stop)
        self.controls.scrubbed.connect(self._on_scrubbed)
        self.controls.seek_requested.connect(self._on_seek)
        self.controls.volume_changed.connect(self._on_volume_changed)
        self.controls.speed_changed.connect(self._on_speed_changed)
        self.controls.load_song_clicked.connect(self._on_load_song)
        self.controls.unload_song_clicked.connect(self._on_unload_song)
        self._connect_backend(backend)
        self._sync_transport_ui()
        self._controller.set_volume(self.controls.volume)   # volume awal slider → backend audio
        self._controller.set_speed(self.controls.speed)     # kecepatan awal dropdown → backend audio

    # ── API untuk MainWindow ─────────────────────────────────────────────
    @property
    def controller(self) -> PreviewController:
        return self._controller

    def set_session(self, session: PreviewSession) -> None:
        """Pasang data chart terkini (dipanggil saat dibuka, chart berganti, atau teks berubah)."""
        if self._disposed:
            return
        self._controller.apply_session(session)
        self.controls.set_duration(self._controller.duration_ms())
        self._refresh_availability()
        self._sync_transport_ui()
        self._tick(force=True)

    def dispose(self) -> None:
        """Lepas semua resource (timer, audio). Dipanggil MainWindow saat aplikasi ditutup."""
        if self._disposed:
            return
        self._disposed = True
        self._timer.stop()
        self._controller.dispose()
        self.close()
        self.deleteLater()

    # ── backend signals ──────────────────────────────────────────────────
    def _connect_backend(self, backend) -> None:
        for name, slot in (("error_occurred", self._on_audio_error),
                           ("duration_changed", self._on_duration_changed),
                           ("media_ended", self._on_media_ended)):
            signal = getattr(backend, name, None)
            if signal is not None:
                signal.connect(slot)

    def _on_audio_error(self, message: str) -> None:
        self._controller.notify_audio_error(message)
        self._refresh_availability()
        self._sync_transport_ui()
        self._tick(force=True)

    def _on_duration_changed(self, ms: int) -> None:
        self.controls.set_duration(ms)

    def _on_media_ended(self) -> None:
        self._controller.notify_media_ended()
        self._sync_transport_ui()
        self._tick(force=True)

    # ── interaksi pengguna ───────────────────────────────────────────────
    def _on_play_toggled(self) -> None:
        if self._controller.can_play:
            self._controller.toggle()
        self._sync_transport_ui()
        self._tick(force=True)

    def _on_stop(self) -> None:
        self._controller.stop()
        self._sync_transport_ui()
        self._tick(force=True)

    def _on_scrubbed(self, ms: int) -> None:
        """Slider sedang diseret: tampilkan adegan di posisi itu tanpa menyentuh audio."""
        self.viewport.set_scene(self._controller.scene_at_ms(ms))
        self._last_key = None

    def _on_seek(self, ms: int) -> None:
        self._controller.seek_ms(ms)
        self._tick(force=True)

    def _on_volume_changed(self, percent: int) -> None:
        """Slider volume / tombol mute → backend audio (0–100)."""
        self._controller.set_volume(percent)

    def _on_speed_changed(self, rate: float) -> None:
        """Dropdown Speed → backend audio. Lirik ikut karena clock-nya adalah posisi audio."""
        self._controller.set_speed(rate)

    def _on_load_song(self) -> None:
        """Pilih file audio secara manual (sementara; chart asli tidak disentuh)."""
        session = self._controller.session
        start_dir = ""
        if session is not None and session.chart_path:
            start_dir = str(Path(session.chart_path).parent)
        path, _ = QFileDialog.getOpenFileName(self, "Load Song (temporary)", start_dir, AUDIO_FILE_FILTER)
        if not path:
            return
        if not self._controller.load_manual_audio(Path(path)):
            QMessageBox.warning(self, "Load Song", f"Could not open this file:\n{path}")
            return
        self._after_audio_changed()

    def _on_unload_song(self) -> None:
        """Buang audio sementara dan kembali ke audio milik chart (bila ada)."""
        if self._controller.clear_manual_audio():
            self._after_audio_changed()

    def _after_audio_changed(self) -> None:
        self.controls.set_duration(self._controller.duration_ms())
        self._refresh_availability()
        self._sync_transport_ui()
        self._tick(force=True)

    # ── tampilan ─────────────────────────────────────────────────────────
    def _tick(self, force: bool = False) -> None:
        if self._disposed or self.controls.slider.is_dragging:
            return
        scene = self._controller.scene()
        key = None if scene is None else scene.key   # None selama transisi → selalu digambar ulang
        if force or scene is None or scene.animating or key != self._last_key:
            self.viewport.set_scene(scene)           # statis: hanya bila tampilan berubah
            self._last_key = key
        self.controls.set_position(self._controller.position_ms())

    def _sync_transport_ui(self) -> None:
        playing = self._controller.state is PlaybackState.PLAYING
        self.controls.set_playing(playing)
        if playing and self.isVisible():
            if not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()

    def _refresh_availability(self) -> None:
        self.controls.set_enabled_for_audio(self._controller.can_play)
        manual = self._controller.manual_audio
        self.controls.set_manual_song(manual.name if manual is not None else None)
        text = self._controller.notice
        self.notice.setText(text)
        self.notice.setVisible(bool(text))

    # ── siklus hidup ─────────────────────────────────────────────────────
    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._sync_transport_ui()
        self._tick(force=True)

    def closeEvent(self, event) -> None:
        """Menutup preview hanya menyembunyikannya: posisi & chart tetap, tetapi musik dijeda
        agar tidak terus berbunyi dari window yang tidak terlihat. MainWindow tidak ikut tertutup."""
        if not self._disposed:
            self._controller.pause()
            self._sync_transport_ui()
        self._timer.stop()
        super().closeEvent(event)
