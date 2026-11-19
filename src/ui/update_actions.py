"""Fitur tersembunyi *Check Update*: klik ganda chip versi di status bar → cek rilis terbaru di GitHub.

Permintaan jaringan memakai QtNetwork (asinkron, ada batas waktu), jadi jendela utama tidak pernah membeku walau
koneksi lambat atau mati. Logika versi/parsing ada di ``services.update_check`` (tanpa GUI).
"""
from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import QMessageBox

from services.constants import APP_VERSION, URL_LATEST_RELEASE_API
from services.update_check import ReleaseInfo, UpdateCheckError, describe_http_error, is_newer, parse_release

REQUEST_TIMEOUT_MS = 10_000
_DIALOG_TITLE = "Check for updates"


class UpdateCheckMixin:
    """Mixin MainWindow. Panggil ``_init_update_check()`` sekali di ``__init__``; pemicunya menyambung ke
    ``check_for_updates()``. Mengharapkan ``statusBar()`` dari QMainWindow."""

    def _init_update_check(self) -> None:
        self._update_net = QNetworkAccessManager(self)          # anak jendela → ikut dibersihkan saat jendela ditutup
        self._update_reply: QNetworkReply | None = None

    def check_for_updates(self) -> None:
        if self._update_reply is not None:                      # pengecekan sebelumnya belum selesai: abaikan pemicu ganda
            return
        request = QNetworkRequest(QUrl(URL_LATEST_RELEASE_API))
        request.setRawHeader(b"Accept", b"application/vnd.github+json")
        request.setRawHeader(b"User-Agent", f"eLJe/{APP_VERSION}".encode("ascii", "replace"))   # GitHub API mewajibkan User-Agent
        request.setTransferTimeout(REQUEST_TIMEOUT_MS)
        self._update_reply = self._update_net.get(request)
        self._update_reply.finished.connect(self._on_update_reply)
        self.statusBar().showMessage("Checking for updates…")

    def _on_update_reply(self) -> None:
        reply, self._update_reply = self._update_reply, None
        if reply is None:
            return
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)    # None bila tak ada respons HTTP
        network_error = reply.errorString() if reply.error() != QNetworkReply.NetworkError.NoError else ""
        payload = bytes(reply.readAll())
        reply.deleteLater()
        self.statusBar().clearMessage()

        try:
            if status is None:
                raise UpdateCheckError(f"Could not reach GitHub.\n{network_error}".rstrip())
            if int(status) != 200:
                raise UpdateCheckError(describe_http_error(int(status)))
            info = parse_release(payload)
        except UpdateCheckError as exc:
            QMessageBox.warning(self, _DIALOG_TITLE, str(exc))
            return

        if is_newer(info.tag, APP_VERSION):
            self._show_update_available(info)
        else:
            QMessageBox.information(
                self, _DIALOG_TITLE,
                f"You're up to date.\n\nYou are using {APP_VERSION}; the latest release is {info.tag}.")

    def _show_update_available(self, info: ReleaseInfo) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle("Update available")
        box.setText(f"A new version is available: {info.tag}")
        box.setInformativeText(f"You are using {APP_VERSION}.")
        if info.notes:
            box.setDetailedText(info.notes)
        download = box.addButton("Download", QMessageBox.ButtonRole.AcceptRole)
        later = box.addButton("Later", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(download)
        box.setEscapeButton(later)
        box.exec()
        if box.clickedButton() is download:
            QDesktopServices.openUrl(QUrl(info.url))
