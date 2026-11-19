"""Aksi, menu, toolbar, dan shortcut tag untuk MainWindow."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import QLabel, QMenu, QSizePolicy, QToolBar, QToolButton, QWidget

from core.lyrics.tags import TAG_SHORTCUTS
from services.constants import URL_GUIDE, URL_RELEASE, URL_WEBSITE
from services.settings import SHORTCUTS, update_shortcuts
from ui.live_preview_actions import LIVE_PREVIEW_TOOLTIP
from ui.theme import bind_icon, brand_pixmap_hidpi


class ActionsMixin:
    """Mixin MainWindow: membuat QAction, menu bar, toolbar, dan shortcut tag.

    Mengharapkan atribut MainWindow: plainTextEdit, treeDock, sideDock, dan slot
    open_*/save_file/zoom dari mixin lain."""

    # ── actions ─────────────────────────────────────────────────────────────
    def _act(self, text: str, icon_name: str | None = None, shortcut: str | None = None,
             slot=None, checkable: bool = False) -> QAction:
        a = QAction(text, self)
        if icon_name:
            bind_icon(a, "setIcon", icon_name)
        tip = text
        if shortcut:
            seq = QKeySequence(shortcut)
            a.setShortcut(seq)
            tip += f"   {seq.toString(QKeySequence.SequenceFormat.NativeText)}"
        a.setToolTip(tip)
        a.setCheckable(checkable)
        if slot is not None:
            a.triggered.connect(slot)
        return a

    def _build_actions(self) -> None:
        sc = SHORTCUTS
        # File
        self.act_open = self._act("Open", "open", "Ctrl+O", self.open_file)
        self.act_save = self._act("Save", "save", "Ctrl+S", self.save_file)
        self.act_choose_dir = self._act("Select Song Chart Folder", None, None, self.choose_directory)
        self.act_exit = self._act("Exit", None, None, self.close)
        # Edit-ish
        self.act_find = self._act("Find", "find", "Ctrl+F", self.open_find)
        self.act_replace = self._act("Replace", "replace", "Ctrl+H", self.open_replace)
        self.act_zoom_in = self._act("Zoom In", "zoom_in", None, lambda: self.zoom(+1))
        self.act_zoom_in.setShortcuts([QKeySequence("Ctrl+="), QKeySequence("Ctrl++")])
        self.act_zoom_in.setToolTip("Zoom In   Ctrl+=")
        self.act_zoom_out = self._act("Zoom Out", "zoom_out", None, lambda: self.zoom(-1))
        self.act_zoom_out.setShortcuts([QKeySequence("Ctrl+-"), QKeySequence("Ctrl+Shift+-")])
        self.act_zoom_out.setToolTip("Zoom Out   Ctrl+-")
        # Tools
        self.act_picker = self._act("Color Picker", "picker", sc["colorpicker"], self.color_picker)
        self.act_symbol = self._act("Get Symbol", "symbol", sc["getsymbol"], self.open_symbol)
        self.act_weird = self._act("Weird Text Generator", "weird", sc["weirdtext"], self.open_weird)
        # Jutsu
        self.act_add_jutsu = self._act("Add Jutsu", "add", sc["addjutsu"], self.open_add_jutsu)
        self.act_batch_jutsu = self._act("Batch Jutsu", "lines", sc["batchjutsu"], self.open_batch_jutsu)
        self.act_color_jutsu = self._act("Lyric Color no Jutsu (method 1)", "palette", sc["colorjutsu1"], self.open_lyric_color_1)
        self.act_lyricolor = self._act("Lyric Color no Jutsu (method 2)", "lyricolor", sc["colorjutsu2"], self.open_lyric_color_2)
        self.act_kan2rom = self._act("Kan2Rom no Jutsu", "kan2rom", sc["kan2romjutsu"], self.open_kan2rom)
        # Setting
        self.act_font = self._act("Font", None, None, self.font_setting)
        self.act_highlight = self._act("Highlight", None, None, self.open_highlight)
        self.act_lyric_item = self._act("LyricJutsu", None, None, self.open_lyric_settings)
        self.act_hotkey = self._act("Hotkey", None, None, self.open_hotkeys)
        self.act_appearance = self._act("Appearance", None, None, self.open_appearance)
        # Jutsu Editor (membuka sub-window; bukan toggle)
        self.act_jutsu_editor = self._act("Jutsu Editor", "jutsu_editor", sc["jutsueditor"], self.open_jutsu_editor)
        # View (checkable)
        self.act_toggle_display = self._act("RichText Lyrics", "display", sc["toggle_display"], checkable=True)
        self.act_toggle_tree = self._act("Directory", "sidebar_left", sc["toggle_treeview"], checkable=True)
        self.act_toggle_side = self._act("TempText", "sidebar_right", sc["toggle_temptext"], checkable=True)
        # Live Lyrics Preview (bukan checkable: membuka/mengaktifkan window terpisah)
        self.act_live_preview = self._act("Live Preview", "live_preview", sc["livepreview"], self.open_live_preview)
        preview_tip = LIVE_PREVIEW_TOOLTIP
        if sc["livepreview"]:
            seq = QKeySequence(sc["livepreview"]).toString(QKeySequence.SequenceFormat.NativeText)
            preview_tip += f"   {seq}"
        self.act_live_preview.setToolTip(preview_tip)
        # Help
        self.act_website = self._act("Website", None, None, lambda: QDesktopServices.openUrl(QUrl(URL_WEBSITE)))
        self.act_guide = self._act("Guide/Tutorials", None, None, lambda: QDesktopServices.openUrl(QUrl(URL_GUIDE)))
        self.act_release = self._act("GitHub Release", None, None, lambda: QDesktopServices.openUrl(QUrl(URL_RELEASE)))
        self.act_about = self._act("About", None, None, self.show_about)

        self._shortcut_actions = {
            "jutsueditor": self.act_jutsu_editor, "livepreview": self.act_live_preview,
            "toggle_display": self.act_toggle_display, "toggle_treeview": self.act_toggle_tree,
            "toggle_temptext": self.act_toggle_side, "colorpicker": self.act_picker,
            "getsymbol": self.act_symbol, "weirdtext": self.act_weird,
            "addjutsu": self.act_add_jutsu, "batchjutsu": self.act_batch_jutsu,
            "colorjutsu1": self.act_color_jutsu, "colorjutsu2": self.act_lyricolor,
            "kan2romjutsu": self.act_kan2rom,
        }

    # ── menu bar ────────────────────────────────────────────────────────────
    def _build_menus(self) -> None:
        mb = self.menuBar()

        brand = QLabel()
        dpr = self.devicePixelRatioF()
        brand.setPixmap(brand_pixmap_hidpi(20, dpr))
        brand.setContentsMargins(12, 0, 6, 0)
        mb.setCornerWidget(brand, Qt.Corner.TopLeftCorner)

        m_file = mb.addMenu("File")
        m_file.addAction(self.act_open)
        m_file.addAction(self.act_save)
        m_file.addAction(self.act_choose_dir)
        m_file.addSeparator()
        m_file.addAction(self.act_exit)

        m_set = mb.addMenu("Setting")
        for a in (self.act_appearance, self.act_font, self.act_highlight, self.act_lyric_item, self.act_hotkey):
            m_set.addAction(a)

        m_view = mb.addMenu("View")
        m_view.addAction(self.act_jutsu_editor)
        m_view.addAction(self.act_live_preview)
        m_view.addSeparator()
        for a in (self.act_toggle_display, self.act_toggle_tree, self.act_toggle_side):
            m_view.addAction(a)
        m_view.addSeparator()
        m_view.addAction(self.act_zoom_in)
        m_view.addAction(self.act_zoom_out)

        m_help = mb.addMenu("Help")
        for a in (self.act_website, self.act_guide, self.act_release, self.act_about):
            m_help.addAction(a)

    # ── toolbar ─────────────────────────────────────────────────────────────
    def _build_toolbar(self) -> None:
        tb = QToolBar("Main toolbar", self)
        tb.setObjectName("mainToolbar")
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setIconSize(QSize(20, 20))
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        tb.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)
        self.toolbar = tb

        groups = (
            (self.act_open, self.act_save),
            (self.act_find, self.act_replace, self.act_zoom_in, self.act_zoom_out),
            (self.act_picker, self.act_symbol, self.act_weird),
        )
        for i, group in enumerate(groups):
            if i:
                tb.addSeparator()
            for a in group:
                tb.addAction(a)

        # Grup Jutsu: satu tombol menu dropdown (Add Jutsu, Batch Jutsu, Lyric Color 1 & 2, Kan2Rom)
        tb.addSeparator()
        jutsu_menu = QMenu(self)
        for a in (self.act_add_jutsu, self.act_batch_jutsu, self.act_color_jutsu, self.act_lyricolor, self.act_kan2rom):
            jutsu_menu.addAction(a)
        jutsu_btn = QToolButton(tb)
        jutsu_btn.setMenu(jutsu_menu)
        jutsu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        jutsu_btn.setText("Jutsu")
        jutsu_btn.setToolTip("Jutsu menu")
        jutsu_btn.setIconSize(QSize(20, 20))
        bind_icon(jutsu_btn, "setIcon", "wand")
        jutsu_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        jutsu_btn.setProperty("chip", True)
        jutsu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tb.addWidget(jutsu_btn)

        for a in (self.act_jutsu_editor, self.act_live_preview):   # aksi lain: ikon + label
            tb.addAction(a)
            btn = tb.widgetForAction(a)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            btn.setProperty("chip", True)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        for a in (self.act_toggle_display, self.act_toggle_tree, self.act_toggle_side):   # toggle: ikon saja
            tb.addAction(a)

        for a in tb.actions():
            w = tb.widgetForAction(a)
            if w is not None and w is not spacer:
                w.setCursor(Qt.CursorShape.PointingHandCursor)

    # ── tag shortcuts (Ctrl+B, Ctrl+I, …) ───────────────────────────────────
    def _build_tag_shortcuts(self) -> None:
        self._tag_shortcuts = []
        for name, tag, attr in TAG_SHORTCUTS:
            sc = QShortcut(QKeySequence(SHORTCUTS[name]), self)
            sc.activated.connect(lambda t=tag, a=attr: self.insert_tag(t, a))
            self._tag_shortcuts.append(sc)

    def insert_tag(self, tag: str, attr: str | None) -> None:
        cur = self.plainTextEdit.textCursor()
        if attr is None:                                   # <br> tanpa penutup
            cur.insertText(f"<{tag}>")
        else:
            selected, close = cur.selectedText(), f"</{tag}>"
            cur.insertText(f"<{tag}{attr}>{selected}{close}")
            if not selected:                               # kursor masuk di antara tag
                cur.movePosition(QTextCursor.MoveOperation.Left,
                                 QTextCursor.MoveMode.MoveAnchor, len(close))
        self.plainTextEdit.setTextCursor(cur)
        self.plainTextEdit.setFocus()

    def _apply_shortcuts(self, data: dict) -> None:
        data = update_shortcuts(data)                   # validasi + perbarui SHORTCUTS + simpan; pakai hasil validasinya
        for key, act in self._shortcut_actions.items():
            seq = QKeySequence(data[key])
            act.setShortcut(seq)
            act.setToolTip(f"{act.text()}   {seq.toString(QKeySequence.SequenceFormat.NativeText)}")
        for (name, _tag, _attr), sc in zip(TAG_SHORTCUTS, self._tag_shortcuts):
            sc.setKey(QKeySequence(data[name]))
