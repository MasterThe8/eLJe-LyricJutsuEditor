"""Kontrol playback: tombol Play/Pause, Stop, slider seek, waktu sekarang / total."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QSlider, QStyle, QToolButton, QVBoxLayout, QStyleOptionSlider
)

from core.preview.controller import DEFAULT_SPEED, SPEED_OPTIONS, format_speed, format_time
from ui.theme import icon, mono_font, theme_events

DISCLAIMER_TEXT = "This feature is not 100% identical to the in-game version."


class SeekSlider(QSlider):
    """Slider horizontal dengan klik-untuk-lompat dan pratinjau saat diseret.

    * ``scrubbed(ms)``       — nilai berubah selama pengguna menyeret/menekan (belum seek sungguhan).
    * ``seek_requested(ms)`` — pengguna melepas mouse / memakai keyboard → lakukan seek.
    Pembaruan dari kode (``set_position``) tidak memancarkan sinyal apa pun.
    """

    scrubbed = Signal(int)
    seek_requested = Signal(int)

    KEY_STEP_MS = 5_000

    def __init__(self, parent=None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setObjectName("seekSlider")
        self.setRange(0, 0)
        self.setFixedHeight(28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._dragging = False

    @property
    def is_dragging(self) -> bool:
        return self._dragging

    def set_position(self, ms: int) -> None:
        if self._dragging or self.value() == ms:
            return
        self.blockSignals(True)
        self.setValue(ms)
        self.blockSignals(False)

    def set_duration(self, ms: int) -> None:
        self.blockSignals(True)
        self.setRange(0, max(0, ms))
        self.blockSignals(False)

    def _value_at(self, x: float) -> int:
        x = max(0, min(int(x), self.width()))
        return QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), x, max(1, self.width()))

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled() and self.maximum() > 0:
            self._dragging = True
            value = self._value_at(event.position().x())
            self.blockSignals(True)
            self.setValue(value)
            self.blockSignals(False)
            self.scrubbed.emit(value)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._dragging:
            value = self._value_at(event.position().x())
            self.blockSignals(True)
            self.setValue(value)
            self.blockSignals(False)
            self.scrubbed.emit(value)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._dragging and event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self.seek_requested.emit(self.value())
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        step = {Qt.Key.Key_Left: -self.KEY_STEP_MS, Qt.Key.Key_Right: self.KEY_STEP_MS}.get(event.key())
        if step is not None and self.isEnabled() and self.maximum() > 0:
            self.seek_requested.emit(max(0, min(self.value() + step, self.maximum())))
            event.accept()
            return
        super().keyPressEvent(event)


class VolumeSlider(QSlider):
    """Horizontal volume slider with direct pointer positioning."""

    def __init__(self, parent=None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)

        self.setObjectName("volumeSlider")
        self.setRange(0, 100)
        self.setSingleStep(1)
        self.setPageStep(5)
        self.setTracking(True)
        self.setFixedSize(120, 28)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def _value_at(self, x: float) -> int:
        option = QStyleOptionSlider()
        self.initStyleOption(option)

        groove = self.style().subControlRect(
            QStyle.ComplexControl.CC_Slider,
            option,
            QStyle.SubControl.SC_SliderGroove,
            self,
        )

        handle = self.style().subControlRect(
            QStyle.ComplexControl.CC_Slider,
            option,
            QStyle.SubControl.SC_SliderHandle,
            self,
        )

        slider_length = handle.width()

        slider_min = groove.x()
        slider_max = groove.right() - slider_length + 1

        position = int(x - slider_length / 2)
        position = max(slider_min, min(position, slider_max))

        span = max(1, slider_max - slider_min)

        return QStyle.sliderValueFromPosition(
            self.minimum(),
            self.maximum(),
            position - slider_min,
            span,
            option.upsideDown,
        )

    def mousePressEvent(self, event) -> None:
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.isEnabled()
        ):
            self.setSliderDown(True)
            self.setValue(self._value_at(event.position().x()))
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self.isSliderDown():
            self.setValue(self._value_at(event.position().x()))
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.isSliderDown()
        ):
            self.setValue(self._value_at(event.position().x()))
            self.setSliderDown(False)
            event.accept()
            return

        super().mouseReleaseEvent(event)

class SpeedComboBox(QComboBox):
    """Dropdown kecepatan. Roda mouse diabaikan agar kecepatan tidak berubah tanpa sengaja."""

    def wheelEvent(self, event) -> None:
        event.ignore()


class PlaybackControls(QFrame):
    """Panel kontrol di bagian bawah window. Tidak memegang state playback — hanya menampilkan dan
    meneruskan niat pengguna lewat sinyal."""

    play_toggled = Signal()
    stop_clicked = Signal()
    scrubbed = Signal(int)
    seek_requested = Signal(int)
    volume_changed = Signal(int)                       # 0–100
    speed_changed = Signal(float)                      # 0.5 … 2.0 (1.0 = normal)
    load_song_clicked = Signal()                       # minta dialog "Load Song" (audio sementara)
    unload_song_clicked = Signal()                     # kembali ke audio milik chart

    _LOAD_TIP = ("Load a song manually (temporary). Useful when the chart's audio is missing; "
                 "the chart file is not modified.")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("previewControls")
        self._playing = False

        self.btn_play = self._button("Play / Pause   Space")
        self.btn_stop = self._button("Stop")
        self.slider = SeekSlider()
        self.lbl_pos = QLabel(format_time(0))
        self.lbl_dur = QLabel(format_time(0))
        for lbl in (self.lbl_pos, self.lbl_dur):
            lbl.setObjectName("timeLabel")
            lbl.setFont(mono_font(10))
            lbl.setMinimumWidth(lbl.fontMetrics().horizontalAdvance("00:00.000") + 6)
        self.lbl_dur.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._volume = 100
        self._last_volume = 100
        self.btn_mute = self._button("Mute")
        self.slider_volume = VolumeSlider()
        self.slider_volume.setValue(self._volume)
        self.slider_volume.setToolTip("Volume")

        # Speed: dropdown di bawah kontrol volume. Aktif sebelum audio siap (seperti volume).
        self.lbl_speed = QLabel("Speed")
        self.lbl_speed.setObjectName("speedLabel")
        self.combo_speed = SpeedComboBox()
        self.combo_speed.setObjectName("speedCombo")
        for rate in SPEED_OPTIONS:
            self.combo_speed.addItem(format_speed(rate), rate)
        self.combo_speed.setCurrentIndex(SPEED_OPTIONS.index(DEFAULT_SPEED))
        self.combo_speed.setToolTip("Playback speed (music + lyrics)")
        self.combo_speed.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_speed.setFocusPolicy(Qt.FocusPolicy.NoFocus)     # Space tetap untuk Play/Pause
        self._speed = DEFAULT_SPEED

        # Load Song: memuat audio sementara bila audio chart tidak ada (tidak mengubah file chart).
        self.btn_load_song = self._button(self._LOAD_TIP)
        self.btn_load_song.setText("Load Song")
        self.btn_load_song.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.btn_load_song.setIconSize(QSize(16, 16))
        self.btn_load_song.setProperty("chip", True)
        self.btn_unload_song = self._button("Remove the temporary song and use the chart's own audio")
        self.btn_unload_song.setIconSize(QSize(16, 16))
        self.btn_unload_song.hide()

        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(self.lbl_pos)
        row.addWidget(self.slider, 1)
        row.addWidget(self.lbl_dur)
        row.addWidget(self.btn_mute)
        row.addWidget(self.slider_volume)

        # Baris bawah 3 kolom: [Load Song] · [Play Stop] · [Speed ▾]. Kolom kiri & kanan sama-sama
        # stretch 1 sehingga Play/Stop tetap di tengah, dan Speed rata kanan tepat di bawah volume.
        left = QHBoxLayout()
        left.setSpacing(4)
        left.addWidget(self.btn_load_song)
        left.addWidget(self.btn_unload_song)
        left.addStretch(1)

        center = QHBoxLayout()
        center.setSpacing(4)
        center.addWidget(self.btn_play)
        center.addWidget(self.btn_stop)

        right = QHBoxLayout()
        right.setSpacing(6)
        right.addStretch(1)
        right.addWidget(self.lbl_speed)
        right.addWidget(self.combo_speed)

        buttons = QGridLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setHorizontalSpacing(8)
        buttons.addLayout(left, 0, 0)
        buttons.addLayout(center, 0, 1)
        buttons.addLayout(right, 0, 2)
        buttons.setColumnStretch(0, 1)
        buttons.setColumnStretch(2, 1)

        # Catatan kecil di pojok kiri bawah panel kontrol.
        self.disclaimer = QLabel(DISCLAIMER_TEXT)
        self.disclaimer.setObjectName("previewDisclaimer")
        self.disclaimer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(0)
        footer.addWidget(self.disclaimer)
        footer.addStretch(1)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(4)
        lay.addLayout(row)                             # slider + durasi di atas
        lay.addLayout(buttons)                         # Play/Pause + Stop di bawah, terpusat
        lay.addLayout(footer)                          # disclaimer rata kiri di pojok bawah

        self.btn_play.clicked.connect(self.play_toggled)
        self.btn_stop.clicked.connect(self.stop_clicked)
        self.slider.scrubbed.connect(self._on_scrubbed)
        self.slider.seek_requested.connect(self.seek_requested)
        self.btn_mute.clicked.connect(self._toggle_mute)
        self.slider_volume.valueChanged.connect(self._on_volume_changed)
        self.combo_speed.currentIndexChanged.connect(self._on_speed_index_changed)
        self.btn_load_song.clicked.connect(self.load_song_clicked)
        self.btn_unload_song.clicked.connect(self.unload_song_clicked)
        theme_events.changed.connect(self._apply_icons)
        self._apply_icons()
        self.set_enabled_for_audio(False)

    def _button(self, tip: str) -> QToolButton:
        b = QToolButton()
        b.setToolTip(tip)
        b.setIconSize(QSize(20, 20))
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setAutoRaise(True)
        b.setFocusPolicy(Qt.FocusPolicy.NoFocus)      # Space ditangani window; cegah pemicuan ganda
        return b

    # ── API untuk window ─────────────────────────────────────────────────
    def set_playing(self, playing: bool) -> None:
        self._playing = playing
        self._apply_icons()

    def set_enabled_for_audio(self, enabled: bool) -> None:
        """Aktifkan kontrol transport. Volume & mute tetap aktif: volumenya bisa diatur
        sebelum audio siap dan tidak bergantung pada file chart."""
        for w in (self.btn_play, self.btn_stop, self.slider):
            w.setEnabled(enabled)

    @property
    def volume(self) -> int:
        """Volume aktif 0–100."""
        return self._volume

    def set_volume(self, percent: int) -> None:
        """Sinkronkan slider tanpa memancarkan ``volume_changed``."""
        self._volume = max(0, min(100, int(percent)))
        self.slider_volume.blockSignals(True)
        self.slider_volume.setValue(self._volume)
        self.slider_volume.blockSignals(False)
        if self._volume > 0:
            self._last_volume = self._volume
        self._apply_icons()

    @property
    def speed(self) -> float:
        """Kecepatan playback aktif (1.0 = normal)."""
        return self._speed

    def set_speed(self, rate: float) -> None:
        """Sinkronkan dropdown tanpa memancarkan ``speed_changed``. Nilai di luar daftar diabaikan."""
        index = self.combo_speed.findData(rate)
        if index < 0:
            return
        self._speed = float(rate)
        self.combo_speed.blockSignals(True)
        self.combo_speed.setCurrentIndex(index)
        self.combo_speed.blockSignals(False)

    def set_manual_song(self, name: str | None) -> None:
        """Tampilkan status audio sementara: tombol "kembali ke audio chart" hanya saat ada."""
        active = bool(name)
        self.btn_unload_song.setVisible(active)
        self.btn_load_song.setToolTip(f"Temporary song: {name}\nClick to choose another file." if active
                                      else self._LOAD_TIP)

    def set_duration(self, ms: int) -> None:
        self.slider.set_duration(ms)
        self.lbl_dur.setText(format_time(ms))

    def set_position(self, ms: int) -> None:
        self.slider.set_position(ms)
        self._set_text(self.lbl_pos, format_time(ms))

    # ── internal ─────────────────────────────────────────────────────────
    def _on_scrubbed(self, ms: int) -> None:
        self._set_text(self.lbl_pos, format_time(ms))
        self.scrubbed.emit(ms)

    def _on_volume_changed(self, value: int) -> None:
        self._volume = int(value)
        if self._volume > 0:
            self._last_volume = self._volume
        self._apply_icons()
        self.volume_changed.emit(self._volume)

    def _on_speed_index_changed(self, index: int) -> None:
        rate = self.combo_speed.itemData(index)
        if rate is None:
            return
        self._speed = float(rate)
        self.speed_changed.emit(self._speed)

    def _toggle_mute(self) -> None:
        if self.slider_volume.value() > 0:
            self._last_volume = self.slider_volume.value()
            self.slider_volume.setValue(0)
        else:
            self.slider_volume.setValue(self._last_volume or 100)

    @staticmethod
    def _set_text(label: QLabel, text: str) -> None:
        if label.text() != text:                      # hindari relayout/repaint yang tak perlu per frame
            label.setText(text)

    def _apply_icons(self, _theme_id: str = "") -> None:
        self.btn_play.setIcon(icon("pause" if self._playing else "play", "TEXT", "ACCENT", "ACCENT", "FAINT"))
        self.btn_stop.setIcon(icon("stop", "TEXT", "ACCENT", "ACCENT", "FAINT"))
        self.btn_mute.setIcon(icon("volume_mute" if self._volume == 0 else "volume",
                                   "TEXT", "ACCENT", "ACCENT", "FAINT"))
        self.btn_load_song.setIcon(icon("open", "TEXT", "ACCENT", "ACCENT", "FAINT"))
        self.btn_unload_song.setIcon(icon("reset", "TEXT", "ACCENT", "ACCENT", "FAINT"))
