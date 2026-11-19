"""Integrasi Live Lyrics Preview ke MainWindow: tombol, satu instance window, sinkron dengan chart.

Mixin MainWindow. Mengharapkan atribut: ``_chart_doc`` (FileActionsMixin), ``plainTextEdit``.
"""
from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

from core.preview.session import PreviewSession, build_preview_session_from_document
from ui.lyrics_preview import LiveLyricsPreviewWindow

LIVE_PREVIEW_TOOLTIP = "Open Live Lyrics Preview"
_EDIT_DEBOUNCE_MS = 250           # jeda setelah mengetik sebelum lirik di-parse ulang


class LivePreviewMixin:
    """Satu instance ``LiveLyricsPreviewWindow`` per MainWindow, dibuat saat pertama dibuka."""

    _live_preview_window: LiveLyricsPreviewWindow | None = None

    def _init_live_preview(self) -> None:
        self._live_preview_timer = QTimer(self)
        self._live_preview_timer.setSingleShot(True)
        self._live_preview_timer.setInterval(_EDIT_DEBOUNCE_MS)
        self._live_preview_timer.timeout.connect(self._refresh_live_preview)

    # ── dibuka dari tombol ───────────────────────────────────────────────
    def open_live_preview(self) -> None:
        if self._chart_doc is None:
            QMessageBox.information(
                self, "Live Preview",
                "No chart file is currently open.\nPlease open a .chart file first.")
            return
        win = self._live_preview_window
        if win is None:
            win = LiveLyricsPreviewWindow(self)
            self._live_preview_window = win
        win.set_session(self._build_live_preview_session())
        if win.isMinimized():
            win.showNormal()
        else:
            win.show()
        win.raise_()
        win.activateWindow()

    # ── sinkronisasi ─────────────────────────────────────────────────────
    def _build_live_preview_session(self) -> PreviewSession:
        # Teks editor (bukan doc.events_body): lirik yang belum disimpan pun langsung ter-preview.
        return build_preview_session_from_document(self._chart_doc, self.plainTextEdit.toPlainText())

    def _live_preview_active(self) -> bool:
        win = self._live_preview_window
        return win is not None and self._chart_doc is not None

    def _schedule_live_preview_refresh(self) -> None:
        """Dipanggil tiap teks editor berubah. Hanya bekerja bila window sedang terlihat; saat
        tersembunyi cukup di-refresh ketika dibuka lagi (open_live_preview selalu membangun ulang)."""
        if self._live_preview_active() and self._live_preview_window.isVisible():
            self._live_preview_timer.start()

    def _refresh_live_preview(self) -> None:
        if not self._live_preview_active():
            return
        try:
            self._live_preview_window.set_session(self._build_live_preview_session())
        except Exception as exc:                                    # noqa: BLE001
            # Preview adalah fitur tambahan: kegagalannya tidak boleh mengganggu buka/simpan/ketik.
            self.statusBar().showMessage(f"Live Preview could not refresh: {exc}", 6000)

    def _on_live_preview_chart_changed(self) -> None:
        """Chart baru dibuka / file disimpan (path bisa berubah → audio bisa berbeda): segarkan SEKARANG."""
        self._live_preview_timer.stop()
        self._refresh_live_preview()

    # ── penutupan aplikasi ───────────────────────────────────────────────
    def _shutdown_live_preview(self) -> None:
        self._live_preview_timer.stop()
        win, self._live_preview_window = self._live_preview_window, None
        if win is not None:
            win.dispose()
