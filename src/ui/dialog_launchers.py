"""Pembuka dialog dan penghubung signal-nya ke MainWindow."""
from __future__ import annotations

import re

from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor, QDesktopServices, QFontInfo, QGuiApplication, QTextCursor, QTextDocument
from PySide6.QtWidgets import QMessageBox

from core.text_tools.weird_text import convert_all
from services.constants import APP_NAME, APP_VERSION
from services.defaults import DEFAULT_PICKER_COLOR
from services.settings import (
    HIGHLIGHT,
    LYRIC_SETTINGS,
    SHORTCUTS,
    update_editor_fonts,
    update_highlight,
    update_lyric_settings,
)
from services.text_assets import SYMBOLS_FILE, WEIRD_TEXT_DIR, read_weird_styles
from ui.dialogs.about import AboutDialog
from ui.dialogs.color_dialog import ColorDialog
from ui.dialogs.find_replace import FindDialog, ReplaceDialog
from ui.dialogs.jutsu_editor import JutsuEditorWindow
from ui.dialogs.operations.add_lyric import AddJutsuDialog
from ui.dialogs.operations.batch_jutsu import BatchJutsuDialog
from ui.dialogs.operations.convert_phrase import Kan2RomDialog
from ui.dialogs.operations.lyric_color import LyricColorMethod1Dialog, LyricColorMethod2Dialog
from ui.dialogs.settings.appearance import AppearanceDialog
from ui.dialogs.settings.font import FontDialog
from ui.dialogs.settings.highlight import HighlightDialog
from ui.dialogs.settings.hotkeys import HotkeyDialog
from ui.dialogs.settings.lyric_items import LyricSettingDialog
from ui.dialogs.symbol_picker import SymbolWindow
from ui.dialogs.weird_text import WeirdTextDialog
from ui.jutsu_actions import JUTSU_ADD, JUTSU_BATCH, JUTSU_KAN2ROM, JUTSU_LYRIC_COLOR_1, JUTSU_LYRIC_COLOR_2
from ui.widgets.highlighter import LyricHighlighter


class DialogLaunchersMixin:
    """Mixin MainWindow: membuka dialog Find/Replace/Color/Weird/Setting/Symbol/Jutsu/Jutsu Editor.

    Dialog non-modal dibuat sekali lalu dipakai ulang lewat _show_tool()."""

    # ── dialogs ─────────────────────────────────────────────────────────────
    def _show_tool(self, attr: str, factory):
        """Dialog non-modal: dibuat sekali, lalu ditampilkan ulang."""
        dlg = getattr(self, attr, None)
        if dlg is None:
            dlg = factory()
            setattr(self, attr, dlg)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()
        return dlg

    # Find ------------------------------------------------------------------
    def open_find(self) -> None:
        def make():
            d = FindDialog(self)
            d.find_requested.connect(self._do_find)
            return d
        self._show_tool("_find_dialog", make)

    def _do_find(self, text: str, backward: bool, match_case: bool, whole_word: bool) -> None:
        """Pencarian minimal bawaan Qt. TODO(port): samakan dengan perilaku find_text() asli."""
        F = QTextDocument.FindFlag
        flags = F(0)
        if backward:
            flags |= F.FindBackward
        if match_case:
            flags |= F.FindCaseSensitively
        if whole_word:
            flags |= F.FindWholeWords
        self.tabWidget.setCurrentWidget(self.plainTextEdit)
        found = self.plainTextEdit.find(text, flags)
        if not found:                                           # putar balik ke awal/akhir
            cur = self.plainTextEdit.textCursor()
            cur.movePosition(QTextCursor.MoveOperation.End if backward else QTextCursor.MoveOperation.Start)
            self.plainTextEdit.setTextCursor(cur)
            found = self.plainTextEdit.find(text, flags)
        self._find_dialog.set_status("" if found else "No matches")

    # Replace ---------------------------------------------------------------
    def open_replace(self) -> None:
        dlg = ReplaceDialog(self)
        dlg.replace_all_requested.connect(self._do_replace_all)
        dlg.exec()

    def _do_replace_all(self, text: str, replacement: str, match_case: bool) -> None:
        """Versi minimal. TODO(port): pakai getScript() / alur Replace asli."""
        src = self.plainTextEdit.toPlainText()
        flags = 0 if match_case else re.IGNORECASE
        new = re.sub(re.escape(text), lambda _m: replacement, src, flags=flags)
        bar = self.plainTextEdit.verticalScrollBar()
        pos = bar.value()
        cur = self.plainTextEdit.textCursor()
        cur.beginEditBlock()                                    # satu langkah undo
        cur.select(QTextCursor.SelectionType.Document)
        cur.insertText(new)
        cur.endEditBlock()
        bar.setValue(pos)
        self.statusBar().showMessage("Replaced all matches", 3000)

    # Select Color ----------------------------------------------------------
    def color_picker(self) -> None:
        last = getattr(self, "_last_color", QColor(DEFAULT_PICKER_COLOR))
        color = ColorDialog.get_color(last, self, "Select Color")
        if color.isValid():
            self._last_color = color
            hex_ = color.name().upper()
            QGuiApplication.clipboard().setText(hex_)
            self.statusBar().showMessage(f"Copied {hex_} to clipboard", 2500)

    # Weird Text ------------------------------------------------------------
    def open_weird(self) -> None:
        def make():
            d = WeirdTextDialog(self)
            d.generate_requested.connect(self._generate_weird)
            return d
        self._show_tool("_weird_dialog", make)

    def _generate_weird(self, text: str) -> None:
        """Ubah ``text`` ke tiap alfabet di ``assets/weird_text`` (wt1…wt26), satu hasil per file.

        File dibaca saat Generate ditekan, jadi hasil edit file gaya langsung terpakai. File yang rusak dilewati
        dan dilaporkan di footer dialog; gaya lainnya tetap tampil.
        """
        styles, problems = read_weird_styles()
        if styles:
            notice = f"{len(problems)} style file(s) skipped" if problems else ""
        else:
            notice = "No weird text styles found"
        self._weird_dialog.set_results(
            convert_all(text, styles), notice, "\n".join(problems) or str(WEIRD_TEXT_DIR))

    # Appearance ------------------------------------------------------------
    def open_appearance(self) -> None:
        if getattr(self, "theme_manager", None) is None:
            self.statusBar().showMessage("Theme manager is not available", 4000)
            return
        AppearanceDialog(self.theme_manager, self).exec()

    # Font ------------------------------------------------------------------
    def font_setting(self) -> None:
        ok, font = FontDialog.get_font(self.plainTextEdit.font(), self)
        if ok:
            self.plainTextEdit.setFont(font)
            self.richTextEdit.setFont(font)
            family = font.family() or QFontInfo(font).family()          # nama kosong = font bawaan sistem → simpan nama nyatanya
            spec = {"family": family, "size": font.pointSize(), "bold": font.bold(), "italic": font.italic()}
            update_editor_fonts({"plain": spec, "rich": spec})          # dialog Font berlaku untuk kedua editor
            self._sync_jutsu_editor_fonts()

    def _sync_jutsu_editor_fonts(self) -> None:
        """Samakan font Jutsu Editor dengan editor utama (dipanggil setelah dialog Font dan Zoom).

        Jutsu Script mengikuti PlainText Lyrics; RichText Lyrics mengikuti Display Lyrics.
        Tidak melakukan apa-apa bila Jutsu Editor belum pernah dibuka (font diberikan saat pembuatan).
        """
        window = getattr(self, "_jutsu_editor_window", None)
        if window is not None:
            window.set_editor_fonts(self.plainTextEdit.font(), self.richTextEdit.font())

    # Highlight -------------------------------------------------------------
    def open_highlight(self) -> None:
        dlg = HighlightDialog(HIGHLIGHT, self)
        dlg.applied.connect(self._apply_highlight)
        dlg.exec()

    def _apply_highlight(self, colors: dict) -> None:
        update_highlight(colors)                        # validasi + perbarui HIGHLIGHT + simpan
        self.highlighter.setDocument(None)
        self.highlighter = LyricHighlighter(self.plainTextEdit.document(), HIGHLIGHT)

    # LyricJutsu ------------------------------------------------------------
    def open_lyric_settings(self) -> None:
        dlg = LyricSettingDialog(LYRIC_SETTINGS, self)
        dlg.set_preview_colors(HIGHLIGHT)
        dlg.applied.connect(update_lyric_settings)      # validasi + perbarui LYRIC_SETTINGS + simpan
        dlg.exec()

    # Hotkey ----------------------------------------------------------------
    def open_hotkeys(self) -> None:
        dlg = HotkeyDialog(SHORTCUTS, self)
        dlg.applied.connect(self._apply_shortcuts)
        dlg.exec()

    # Symbol ----------------------------------------------------------------
    def open_symbol(self) -> None:
        def make():
            d = SymbolWindow(self)
            d.symbol_copied.connect(lambda ch: self.statusBar().showMessage(f"Copied “{ch}” to clipboard", 2500))
            d.show_txt_requested.connect(self._show_symbols_txt)
            return d
        self._show_tool("_symbol_window", make)

    def _show_symbols_txt(self) -> None:
        """Buka ``assets/symbols/CH_Lyric_Symbols.txt`` di aplikasi teks bawaan sistem.

        Perubahan pada file itu baru tampil di Get Symbol / Symbol Picker setelah aplikasi dibuka ulang.
        """
        if not SYMBOLS_FILE.is_file():
            self.statusBar().showMessage(f"Symbol file not found: {SYMBOLS_FILE}", 6000)
        elif not QDesktopServices.openUrl(QUrl.fromLocalFile(str(SYMBOLS_FILE))):
            self.statusBar().showMessage(f"Could not open {SYMBOLS_FILE.name}", 6000)

    # Jutsu -----------------------------------------------------------------
    def _selected_position(self) -> tuple[bool, int | None]:
        """Posisi dari teks terpilih di editor. (False, None) bila pilihan bukan angka."""
        sel = self.plainTextEdit.textCursor().selectedText()
        if not sel:
            return True, None
        if sel.isdigit():
            return True, int(sel)
        QMessageBox.critical(self, "Error", "Select the position value correctly!")
        return False, None

    def _open_jutsu(self, dialog_cls, kind: str) -> None:
        ok, position = self._selected_position()
        if not ok:
            return
        dlg = dialog_cls(self)
        if position is not None:
            dlg.set_position(position)
        dlg.set_lyric_settings(LYRIC_SETTINGS, HIGHLIGHT)
        # Apply → run_jutsu() (JutsuActionsMixin). Bila mengembalikan pesan error, dialog tetap terbuka.
        dlg.apply_handler = lambda payload, kind=kind: self.run_jutsu(kind, payload)
        dlg.exec()

    def open_add_jutsu(self) -> None:
        self._open_jutsu(AddJutsuDialog, JUTSU_ADD)

    def open_batch_jutsu(self) -> None:
        """Batch Jutsu: Add Jutsu untuk banyak baris. Alurnya sama dengan Jutsu lain (``_open_jutsu``)."""
        self._open_jutsu(self._make_batch_dialog, JUTSU_BATCH)

    def _make_batch_dialog(self, parent) -> BatchJutsuDialog:
        dlg = BatchJutsuDialog(parent)
        dlg.script_provider = self.plainTextEdit.toPlainText      # tabel Lyric Input membaca script SAAT dibuka
        return dlg

    def open_lyric_color_1(self) -> None:
        self._open_jutsu(LyricColorMethod1Dialog, JUTSU_LYRIC_COLOR_1)

    def open_lyric_color_2(self) -> None:
        self._open_jutsu(LyricColorMethod2Dialog, JUTSU_LYRIC_COLOR_2)

    def open_kan2rom(self) -> None:
        self._open_jutsu(Kan2RomDialog, JUTSU_KAN2ROM)

    # Jutsu Editor ----------------------------------------------------------
    def open_jutsu_editor(self) -> None:
        """Buka (atau tampilkan ulang) jendela Jutsu Editor; daftarnya ikut berubah saat editor diubah."""
        def make():
            d = JutsuEditorWindow(self.plainTextEdit.toPlainText, self)
            d.set_editor_fonts(self.plainTextEdit.font(), self.richTextEdit.font())   # font = editor utama
            d.apply_handler = self.run_jutsu_edit                   # Apply → JutsuActionsMixin.run_jutsu_edit
            self.plainTextEdit.textChanged.connect(d.schedule_refresh)
            return d
        self._show_tool("_jutsu_editor_window", make)

    # About -----------------------------------------------------------------
    def show_about(self) -> None:
        AboutDialog(self, APP_NAME, APP_VERSION).exec()
