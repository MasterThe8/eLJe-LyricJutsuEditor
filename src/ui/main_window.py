"""Jendela utama eLJe | LyricJutsu Editor (PySide6, GUI only)."""
from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QTextEdit,
    QWidget,
)

from core.chart.validation import check_event_line
from services.constants import APP_NAME, APP_VERSION
from services.settings import EDITOR_FONTS, HIGHLIGHT, PATHS, VIEW, update_editor_fonts, update_view
from ui.actions import ActionsMixin
from ui.dialog_launchers import DialogLaunchersMixin
from ui.file_actions import FileActionsMixin
from ui.jutsu_actions import JutsuActionsMixin
from ui.live_preview_actions import LivePreviewMixin
from ui.preview import build_preview_html
from ui.theme import app_icon, editor_font, mono_font, theme_events
from ui.update_actions import UpdateCheckMixin
from ui.widgets.code_editor import CodeEditor
from ui.widgets.common import DoubleClickLabel
from ui.widgets.directory_panel import DirectoryPanel
from ui.widgets.highlighter import LyricHighlighter
from ui.widgets.side_panel import SidePanel


class MainWindow(ActionsMixin, FileActionsMixin, DialogLaunchersMixin, JutsuActionsMixin, LivePreviewMixin,
                 UpdateCheckMixin, QMainWindow):
    """Jendela utama. Perilaku dipecah ke mixin di actions.py, file_actions.py, dialog_launchers.py,
    jutsu_actions.py, live_preview_actions.py, update_actions.py."""

    def __init__(self, theme_manager=None):
        super().__init__()
        self.theme_manager = theme_manager          # ThemeManager (dimiliki app.py); dipakai dialog Appearance
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.setWindowIcon(app_icon())
        self.setMinimumSize(860, 540)
        self.resize(1240, 760)
        self._center()
        self.last_opened_directory = ""

        self._build_editors()
        self._build_actions()
        self._build_menus()
        self._build_toolbar()
        self._init_live_preview()
        self._build_docks()
        self._build_central()
        self._init_update_check()
        self._build_statusbar()
        self._build_tag_shortcuts()
        self._wire_signals()
        self._apply_defaults()
        theme_events.changed.connect(self._on_theme_changed)

    # ── layout helpers ──────────────────────────────────────────────────────
    def _center(self) -> None:
        geo = self.frameGeometry()
        geo.moveCenter(self.screen().availableGeometry().center())
        self.move(geo.topLeft())

    # ── editors ─────────────────────────────────────────────────────────────
    def _build_editors(self) -> None:
        self.plainTextEdit = CodeEditor()
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.plainTextEdit.setFont(editor_font(EDITOR_FONTS["plain"], mono_font(EDITOR_FONTS["plain"]["size"])))
        self.plainTextEdit.setTabStopDistance(
            4 * self.plainTextEdit.fontMetrics().horizontalAdvance(" "))
        self.highlighter = LyricHighlighter(self.plainTextEdit.document(), HIGHLIGHT)
        # Baris script yang bentuknya salah (bukan `<tick> = E "<event> <input>"`) diberi latar merah. Hanya untuk
        # tab PlainText ini; editor lain (mis. Jutsu editor) bisa berisi potongan baris dan tidak diperiksa.
        self.plainTextEdit.set_line_checker(check_event_line)

        self.richTextEdit = QTextEdit()
        self.richTextEdit.setObjectName("richTextEdit")
        self.richTextEdit.setReadOnly(True)
        self.richTextEdit.document().setDocumentMargin(36)
        self.richTextEdit.setFont(editor_font(EDITOR_FONTS["rich"], QFont(QApplication.font())))

        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(120)

    # ── docks ───────────────────────────────────────────────────────────────
    def _build_docks(self) -> None:
        root = PATHS["chart_dir"]
        if not Path(root).is_dir():
            root = str(Path.home())
        self.dir_panel = DirectoryPanel(root)
        self.treeDock = self._make_dock("Song Chart Directory", "treeDock", self.dir_panel,
                                        Qt.DockWidgetArea.LeftDockWidgetArea)

        self.side_panel = SidePanel()
        self.sideDock = self._make_dock("TempText and Symbol Picker", "sideDock", self.side_panel,
                                        Qt.DockWidgetArea.RightDockWidgetArea)

    def _make_dock(self, title: str, name: str, widget: QWidget, area) -> QDockWidget:
        dock = QDockWidget(title, self)
        dock.setObjectName(name)
        dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        dock.setTitleBarWidget(QWidget())          # header digambar oleh panel sendiri
        dock.setWidget(widget)
        self.addDockWidget(area, dock)
        return dock

    # ── central tabs ────────────────────────────────────────────────────────
    def _build_central(self) -> None:
        self.tabWidget = QTabWidget()
        self.tabWidget.setDocumentMode(True)
        self.tabWidget.tabBar().setDrawBase(False)
        self.tabWidget.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)
        self.tabWidget.addTab(self.plainTextEdit, "PlainText Lyrics")
        self.tabWidget.addTab(self.richTextEdit, "RichText Lyrics")
        self.setCentralWidget(self.tabWidget)

    # ── status bar ──────────────────────────────────────────────────────────
    def _build_statusbar(self) -> None:
        sb = self.statusBar()
        sb.setSizeGripEnabled(False)
        self.lbl_events = QLabel()
        self.lbl_lyrics = QLabel()
        self.lbl_pos = QLabel()
        self.lbl_enc = QLabel("UTF-8")
        for lbl in (self.lbl_events, self.lbl_lyrics, self.lbl_pos, self.lbl_enc):
            lbl.setObjectName("statusChip")
            sb.addPermanentWidget(lbl)
        version = DoubleClickLabel(APP_VERSION)
        version.setObjectName("versionChip")
        version.double_clicked.connect(self.check_for_updates)      # fitur tersembunyi: klik ganda = Check Update
        sb.addPermanentWidget(version)
        sb.showMessage("Ready", 3000)

    # ── signals & initial state ─────────────────────────────────────────────
    def _wire_signals(self) -> None:
        self.act_toggle_tree.toggled.connect(self.treeDock.setVisible)
        self.act_toggle_side.toggled.connect(self.sideDock.setVisible)
        self.act_toggle_display.toggled.connect(self._on_display_toggled)

        self.plainTextEdit.textChanged.connect(self._on_text_changed)
        self.plainTextEdit.textChanged.connect(self._schedule_live_preview_refresh)
        self.plainTextEdit.cursorPositionChanged.connect(self._update_cursor_label)
        self._preview_timer.timeout.connect(self._refresh_preview)

        self.dir_panel.browse_btn.clicked.connect(self.choose_directory)
        self.dir_panel.choose_btn.clicked.connect(self.choose_directory)
        self.dir_panel.tree.clicked.connect(self._on_tree_clicked)
        self.plainTextEdit.document().modificationChanged.connect(self._on_editor_modified)   # tanda * di judul
        self.side_panel.list.clicked.connect(self._copy_symbol)

    def _apply_defaults(self) -> None:
        """Keadaan awal: panel yang tampil mengikuti setting tersimpan; setiap toggle berikutnya langsung disimpan."""
        toggles = (("display", self.act_toggle_display), ("treeview", self.act_toggle_tree),
                   ("temptext", self.act_toggle_side))
        for key, action in toggles:
            action.setChecked(VIEW[key])
        # QAction baru berstatus unchecked: setChecked(False) tidak memancarkan toggled, jadi tanpa baris ini panel
        # yang tersimpan "tersembunyi" tetap tampil. (Dulu tak terlihat karena semua bawaan True.)
        self.treeDock.setVisible(VIEW["treeview"])
        self.sideDock.setVisible(VIEW["temptext"])
        for key, action in toggles:                     # dipasang SETELAH setChecked awal: startup tidak menulis apa pun
            action.toggled.connect(lambda on, key=key: update_view(key, on))
        self._update_counts()
        self._update_cursor_label()
        QTimer.singleShot(0, lambda: self.resizeDocks(
            [self.treeDock, self.sideDock], [270, 330], Qt.Orientation.Horizontal))

    # ── slots: UI behaviour ─────────────────────────────────────────────────
    def _on_text_changed(self) -> None:
        self._update_counts()
        if self.act_toggle_display.isChecked():
            self._preview_timer.start()

    def _on_theme_changed(self, _theme_id: str = "") -> None:
        """Pratinjau HTML menanam warna tema (mis. teks 'Nothing to display yet') → render ulang.
        Isi editor dan warna lirik pengguna tidak disentuh."""
        if self.act_toggle_display.isChecked():
            bar = self.richTextEdit.verticalScrollBar()
            pos = bar.value()
            self._refresh_preview()
            bar.setValue(pos)

    def _on_display_toggled(self, on: bool) -> None:
        if on:
            self._refresh_preview()

    def _refresh_preview(self) -> None:
        self.richTextEdit.setHtml(build_preview_html(self.plainTextEdit.toPlainText()))

    def _update_counts(self) -> None:
        text = self.plainTextEdit.toPlainText()
        events = sum(1 for ln in text.splitlines() if re.match(r"\s*\d+\s*=\s*E\b", ln))
        lyrics = text.count('E "lyric ')
        self.lbl_events.setText(f"{events} events")
        self.lbl_lyrics.setText(f"{lyrics} lyrics")

    def _update_cursor_label(self) -> None:
        cur = self.plainTextEdit.textCursor()
        self.lbl_pos.setText(f"Ln {cur.blockNumber() + 1}, Col {cur.positionInBlock() + 1}")

    def zoom(self, delta: int) -> None:
        for editor in (self.plainTextEdit, self.richTextEdit):
            f = editor.font()
            f.setPointSize(max(8, min(48, f.pointSize() + delta)))
            editor.setFont(f)
        update_editor_fonts({"plain": {"size": self.plainTextEdit.font().pointSize()},
                             "rich": {"size": self.richTextEdit.font().pointSize()}})   # hanya ukuran; jenis font tetap
        self._sync_jutsu_editor_fonts()

    def _copy_symbol(self, index) -> None:
        ch = index.data(Qt.ItemDataRole.DisplayRole)
        if ch:
            QGuiApplication.clipboard().setText(ch)
            self.statusBar().showMessage(f"Copied “{ch}” to clipboard", 2500)

    def _confirm_exit(self) -> bool:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle("Exit")
        box.setText("Are you sure you want to exit?")
        yes = box.addButton("Exit", QMessageBox.ButtonRole.AcceptRole)
        no = box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(no)
        box.exec()
        return box.clickedButton() is yes

    def closeEvent(self, event) -> None:
        # Ada perubahan belum tersimpan → tanya Save / Don't Save / Cancel SAJA (pertanyaan "yakin keluar?" setelah
        # pengguna memilih Don't Save hanya mengganggu). Tanpa perubahan → konfirmasi keluar seperti biasa.
        proceed = self.confirm_unsaved_changes() if self.has_unsaved_changes() else self._confirm_exit()
        if proceed:
            self._shutdown_live_preview()
            event.accept()
        else:
            event.ignore()
