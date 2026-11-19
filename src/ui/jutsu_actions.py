"""Menjalankan Jutsu di editor: payload dialog → ``core.operations`` → teks editor.

Penyusunan teksnya ada di ``core/operations`` (murni Python). File ini hanya menaruh hasilnya di editor.

Semua perubahan ke editor dilakukan lewat ``QTextCursor`` di dalam SATU edit block, sehingga:
  * Ctrl+Z membatalkan satu jutsu penuh, Ctrl+Y mengulanginya (riwayat undo editor tetap utuh);
  * kursor dan posisi scroll tidak lompat.
JANGAN memakai ``setPlainText`` di sini — itu menghapus riwayat undo.
"""
from __future__ import annotations

from PySide6.QtGui import QTextCursor

from core.operations import (
    JutsuError,
    apply_batch_jutsu,
    apply_kan2rom,
    apply_lyric_color_method1,
    apply_jutsu_edit,
    apply_lyric_color_method2,
    build_add_jutsu_text,
    make_patch,
)
from services.settings import LYRIC_SETTINGS

# Identitas jutsu (dipakai DialogLaunchersMixin saat membuka dialog)
JUTSU_ADD = "add"
JUTSU_LYRIC_COLOR_1 = "lyric_color_1"
JUTSU_LYRIC_COLOR_2 = "lyric_color_2"
JUTSU_KAN2ROM = "kan2rom"
JUTSU_BATCH = "batch"


def _qt_position(text: str, index: int) -> int:
    """Indeks karakter Python → posisi QTextCursor (satuan UTF-16, beda untuk emoji / kanji langka)."""
    return len(text[:index].encode("utf-16-le")) // 2


class JutsuActionsMixin:
    """Mixin MainWindow: menerapkan hasil Jutsu ke ``plainTextEdit``. Mengharapkan atribut: plainTextEdit."""

    # ── dipanggil dialog saat tombol Apply ──────────────────────────────────
    def run_jutsu(self, kind: str, payload: dict) -> str:
        """Jalankan satu jutsu. Mengembalikan "" bila sukses, atau pesan error (dialog dibiarkan terbuka)."""
        if kind == JUTSU_BATCH:                                 # payload-nya berbeda (tanpa "position"): jalur sendiri
            return self._run_batch_jutsu(payload)
        closing_lyric = LYRIC_SETTINGS["closing_lyric"]
        hidden_lyric = LYRIC_SETTINGS["hidden_lyric"]
        position = payload["position"]

        try:
            if kind == JUTSU_ADD:
                text = build_add_jutsu_text(
                    payload["jutsu"], position,
                    lyric=payload["lyric"], fake_lyric=payload["fake_lyric"],
                    closing_lyric=closing_lyric, hidden_lyric=hidden_lyric)
                self._replace_current_line(text)
                return ""

            script = self.plainTextEdit.toPlainText()
            if kind == JUTSU_LYRIC_COLOR_1:
                new_script = apply_lyric_color_method1(
                    script, position, color=payload["color"], hidden_lyric=hidden_lyric)
            elif kind == JUTSU_LYRIC_COLOR_2:
                new_script = apply_lyric_color_method2(
                    script, position, color=payload["color"], option=payload["option"],
                    next_lyric=payload["next_lyric"], closing_lyric=closing_lyric, hidden_lyric=hidden_lyric)
            elif kind == JUTSU_KAN2ROM:
                new_script = apply_kan2rom(
                    script, position, kanji=payload["kanji"], color=payload["color"], option=payload["option"],
                    next_lyric=payload["next_lyric"], closing_lyric=closing_lyric, hidden_lyric=hidden_lyric)
            else:
                return f"Unknown jutsu: {kind!r}"
            self._replace_script(script, new_script)
        except JutsuError as exc:
            return str(exc)
        except Exception as exc:                                # noqa: BLE001  — bug tak terduga: tampilkan, jangan crash
            return f"Unexpected error: {type(exc).__name__}: {exc}"
        return ""

    def _run_batch_jutsu(self, payload: dict) -> str:
        """Batch Jutsu: ganti semua baris target sekaligus dalam SATU edit block (satu Ctrl+Z).

        ``apply_batch_jutsu`` menyusun seluruh hasil lebih dulu dan melempar JutsuError bila ada masalah, jadi
        editor tidak pernah berubah setengah jalan. Mengembalikan "" bila sukses, atau pesan error.
        """
        script = self.plainTextEdit.toPlainText()
        try:
            targets = payload["targets"]
            new_script = apply_batch_jutsu(script, payload["jutsu"], targets, payload["rows"])
            self._replace_script(script, new_script)
        except JutsuError as exc:
            return str(exc)
        except Exception as exc:                                # noqa: BLE001  — bug tak terduga: tampilkan, jangan crash
            return f"Unexpected error: {type(exc).__name__}: {exc}"
        count = len(targets)
        self.statusBar().showMessage(f"Batch Jutsu applied to {count} line{'s' if count != 1 else ''} "
                                     "(Ctrl+Z to undo)", 4000)
        return ""

    # ── dipanggil Jutsu Editor saat tombol Apply di salah satu item ─────────
    def run_jutsu_edit(self, block, new_text: str) -> str:
        """Ganti baris ``block`` (hasil scan) dengan ``new_text``, urutkan script, taruh di editor utama.

        Mengembalikan \"\" bila sukses, atau pesan error (item tetap terbuka dengan isiannya).
        """
        script = self.plainTextEdit.toPlainText()
        try:
            new_script = apply_jutsu_edit(script, block, new_text)
            self._replace_script(script, new_script)
        except JutsuError as exc:
            return str(exc)
        except Exception as exc:                                # noqa: BLE001  — bug tak terduga: tampilkan, jangan crash
            return f"Unexpected error: {type(exc).__name__}: {exc}"
        self.statusBar().showMessage("Jutsu applied to the editor (Ctrl+Z to undo)", 4000)
        return ""

    # ── menaruh hasil di editor ─────────────────────────────────────────────
    def _replace_script(self, old_script: str, new_script: str) -> None:
        """Terapkan ``new_script`` (Lyric Color 1/2, Kan2Rom) dengan mengganti HANYA bagian yang berubah."""
        patch = make_patch(old_script, new_script)
        if patch.is_empty:
            return

        editor = self.plainTextEdit
        scroll_bar = editor.verticalScrollBar()
        scroll_pos = scroll_bar.value()

        cursor = QTextCursor(editor.document())            # kursor terpisah: kursor pengguna tidak disentuh
        cursor.beginEditBlock()
        cursor.setPosition(_qt_position(old_script, patch.start))
        cursor.setPosition(_qt_position(old_script, patch.end), QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        if patch.replacement:
            cursor.insertText(patch.replacement)

        # Pengaman: bila editor ternyata berbeda dari ``old_script`` (mis. karakter pemisah baris khusus),
        # ganti seluruh isi — masih di edit block yang sama, jadi tetap satu langkah undo.
        if editor.toPlainText() != new_script:
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.insertText(new_script)
        cursor.endEditBlock()

        scroll_bar.setValue(scroll_pos)

    def _replace_current_line(self, text: str) -> None:
        """Ganti baris tempat kursor berada dengan ``text`` (Add Jutsu).

        Urutan operasinya sama dengan ``delete_current_line()`` + ``insertText()`` aplikasi lama.
        """
        cursor = self.plainTextEdit.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.insertBlock()
        cursor.insertText(text)
        cursor.endEditBlock()
        self.plainTextEdit.setTextCursor(cursor)
