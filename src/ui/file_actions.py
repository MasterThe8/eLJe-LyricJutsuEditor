"""Aksi file MainWindow: buka, simpan, pilih folder."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox

from services.constants import APP_NAME, APP_VERSION
from services.settings import update_chart_dir
from core.chart.document import ChartDocument
from core.chart.parser import parse_chart_file
from core.chart.writer import write_chart_file


class FileActionsMixin:
    """Mixin MainWindow: membuka/menyimpan file .chart dan memilih folder lagu.

    Juga menjaga agar perubahan yang belum disimpan tidak hilang tanpa peringatan (lihat ``confirm_unsaved_changes``):
    dipakai saat membuka chart lain dan saat menutup aplikasi.
    """

    # Dokumen .chart yang sedang aktif
    _chart_doc: ChartDocument | None = None

    # ── helpers ─────────────────────────────────────────────────────────────
    def _start_dir(self) -> str:
        return getattr(self, "last_opened_directory", "") or str(self.dir_panel._root)

    def _save_start_path(self) -> str:
        """Awal dialog Save: path chart yang sedang dibuka (nama filenya ikut diusulkan), atau folder terakhir."""
        path = getattr(self._chart_doc, "file_path", None)
        if path and Path(path).parent.is_dir():
            return path
        return self._start_dir()

    def _set_chart_title(self, path: str) -> None:
        """``[*]`` = tempat Qt menampilkan tanda * (atau titik di macOS) selama ``windowModified`` aktif."""
        self.setWindowTitle(f"{Path(path).name}[*] — {APP_NAME} {APP_VERSION}")

    # ── Unsaved changes ─────────────────────────────────────────────────────
    def has_unsaved_changes(self) -> bool:
        """Chart terbuka dan isi editor berbeda dari saat dibuka / terakhir disimpan.

        Berbasis ``QTextDocument.isModified``: mengurungkan edit (Ctrl+Z) sampai kembali ke keadaan tersimpan otomatis
        dianggap bersih. Tanpa chart terbuka (teks contoh) tidak ada file tujuan simpan, jadi tidak pernah dianggap
        "belum disimpan".
        """
        return self._chart_doc is not None and self.plainTextEdit.document().isModified()

    def _on_editor_modified(self, modified: bool) -> None:
        """Sambungan ``document().modificationChanged``: nyalakan / matikan tanda * di judul jendela."""
        self.setWindowModified(bool(modified) and self._chart_doc is not None)

    def confirm_unsaved_changes(self) -> bool:
        """Pastikan aman melanjutkan aksi yang membuang isi editor (buka chart lain / keluar).

        Tanpa perubahan → ``True`` tanpa bertanya. Bila ada, tanya Save / Don't Save / Cancel:
        Save → ``True`` hanya bila penyimpanan benar-benar berhasil (dialog Save dibatalkan atau gagal → ``False``,
        aksi dibatalkan); Don't Save → ``True``; Cancel / tutup dialog → ``False``.
        """
        if not self.has_unsaved_changes():
            return True
        file_path = getattr(self._chart_doc, "file_path", None)
        name = Path(file_path).name if file_path else "this chart"

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Unsaved changes")
        box.setText(f"Do you want to save the changes you made to “{name}”?")
        box.setInformativeText("Your changes will be lost if you don't save them.")
        save = box.addButton("Save", QMessageBox.ButtonRole.AcceptRole)
        discard = box.addButton("Don't Save", QMessageBox.ButtonRole.DestructiveRole)
        cancel = box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(save)
        box.setEscapeButton(cancel)
        box.exec()

        clicked = box.clickedButton()
        if clicked is save:
            return self.save_file()
        return clicked is discard

    # ── Open File ───────────────────────────────────────────────────────────
    def open_file(self) -> None:
        name, _ = QFileDialog.getOpenFileName(
            self, "Open chart", self._start_dir(), "Chart files (*.chart)"
        )
        if name:
            self.open_chart(name)

    def _on_tree_clicked(self, index) -> None:
        path = self.dir_panel.model.filePath(index)
        if Path(path).is_file():
            self.open_chart(path)

    def open_chart(self, path: str) -> None:
        """Buka chart, tetapi bertanya dulu bila ada perubahan belum tersimpan yang akan tertimpa."""
        if self.confirm_unsaved_changes():
            self.read_chart(path)

    def read_chart(self, path: str) -> None:
        """Baca dan parse file .chart, tampilkan events body di editor."""
        try:
            doc = parse_chart_file(path)
            self._chart_doc = doc
            self.plainTextEdit.setPlainText(doc.events_body)
            self.plainTextEdit.document().setModified(False)        # isi baru = keadaan bersih (titik acuan)
            self.last_opened_directory = str(Path(path).parent)
            self._set_chart_title(path)
            self.setWindowModified(False)
            self.lbl_enc.setText(doc.encoding_label)
            self.lbl_enc.setToolTip(
                doc.encoding_warning or f"Source encoding: {doc.encoding_label}"
            )
            if doc.encoding_warning:
                self.statusBar().showMessage(doc.encoding_warning, 8000)
            else:
                self.statusBar().showMessage(f"Opened {Path(path).name}", 3000)
            self._on_live_preview_chart_changed()                   # chart baru → segarkan Live Preview
        except Exception as exc:                                    # noqa: BLE001
            QMessageBox.critical(self, "Error", f"Error occurred while opening file:\n{exc}")

    # ── Save File ───────────────────────────────────────────────────────────
    def save_file(self) -> bool:
        """Simpan file .chart — gabungkan semua section dan tulis ke disk.

        Mengembalikan ``True`` bila file berhasil ditulis; ``False`` bila tidak ada chart terbuka, dialog Save
        dibatalkan, atau penulisan gagal. (Dipakai ``confirm_unsaved_changes`` untuk memutuskan lanjut / batal.)
        """
        if self._chart_doc is None:
            QMessageBox.warning(
                self, "Warning",
                "No chart file is currently open.\nPlease open a .chart file first."
            )
            return False

        name, _ = QFileDialog.getSaveFileName(
            self, "Save chart", self._save_start_path(), "Chart files (*.chart)"
        )
        if not name:
            return False
        saved = False
        try:
            editor_text = self.plainTextEdit.toPlainText()
            result = write_chart_file(self._chart_doc, name, editor_text)
            saved = True
            self.plainTextEdit.document().setModified(False)        # tersimpan: titik acuan baru
            self.setWindowModified(False)
            self.last_opened_directory = str(Path(name).parent)
            self._set_chart_title(name)
            self.lbl_enc.setText(self._chart_doc.encoding_label)
            self.lbl_enc.setToolTip(
                result.warning or f"Saved as: {self._chart_doc.encoding_label}"
            )
            if result.warning:
                QMessageBox.warning(self, "Encoding changed", result.warning)
            else:
                self.statusBar().showMessage(f"Saved {Path(name).name}", 3000)
            self._on_live_preview_chart_changed()                   # path baru → audio bisa berbeda
        except Exception as exc:                                    # noqa: BLE001
            QMessageBox.critical(self, "Error", f"Error occurred while saving file:\n{exc}")
        return saved

    # ── Choose Directory ────────────────────────────────────────────────────
    def choose_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Select song chart folder", str(self.dir_panel._root)
        )
        if directory:
            self.dir_panel.set_root(directory)
            update_chart_dir(directory)                 # diingat untuk sesi berikutnya
