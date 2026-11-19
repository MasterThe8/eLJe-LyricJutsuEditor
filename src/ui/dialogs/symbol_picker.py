"""Jendela Get Symbol: grid simbol yang disalin ke clipboard saat diklik."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QVBoxLayout,
)

from core.text_tools.symbols import all_symbols, matches, symbol_name
from services.text_assets import AssetError, read_symbols
from ui.dialogs.base import BaseDialog
from ui.html_helpers import gradient_html
from ui.theme import font_for_symbol, mono_font
from ui.widgets.common import add_line_edit_icon, field_label, make_button
from ui.widgets.symbol_grid import configure_symbol_view, symbol_item


class SymbolWindow(BaseDialog):
    """Non-modal. Signal symbol_copied(str) saat sebuah simbol disalin.

    Kategori dan simbolnya dibaca dari ``assets/symbols/CH_Lyric_Symbols.txt`` (``services.text_assets``).
    """
    symbol_copied = Signal(str)
    show_txt_requested = Signal()

    def __init__(self, parent=None):
        super().__init__("Get Symbol", "Symbols that work in Clone Hero lyrics. Click one to copy it.",
                         "symbol", parent, modal=False)
        self.resize(580, 700)
        self.setMinimumSize(480, 540)

        try:
            self._symbols = read_symbols()
            self._load_error = ""
        except AssetError as exc:                       # jendela tetap terbuka; pesan tampil di panel detail
            self._symbols = {}
            self._load_error = str(exc)

        # pencarian
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by symbol, code (2605) or name (star)")
        self.search.setClearButtonEnabled(True)
        add_line_edit_icon(self.search, "find", QLineEdit.ActionPosition.LeadingPosition)
        self.body.addWidget(self.search)

        # kategori + jumlah
        pills = QHBoxLayout()
        pills.setSpacing(6)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self._names = ["All"] + list(self._symbols)
        self._category = "All"
        for i, name in enumerate(self._names):
            b = QPushButton(name)
            b.setObjectName("pill")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            self.group.addButton(b, i)
            pills.addWidget(b)
            if i == 0:
                b.setChecked(True)
        pills.addStretch(1)
        self.count = field_label("", "fieldHint")
        pills.addWidget(self.count)
        self.body.addLayout(pills)

        # grid
        self.list = QListView()
        self.list.setObjectName("symbols")
        self.list.setViewMode(QListView.ViewMode.ListMode)
        self.list.setFlow(QListView.Flow.LeftToRight)
        self.list.setWrapping(True)
        self.list.setResizeMode(QListView.ResizeMode.Adjust)
        self.list.setMovement(QListView.Movement.Static)
        self.list.setUniformItemSizes(True)
        configure_symbol_view(self.list)                # ukuran sel + tanpa elide (lihat symbol_grid)
        self.list.setSpacing(0)
        self.list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list.setCursor(Qt.CursorShape.PointingHandCursor)
        self.model = QStandardItemModel(self.list)
        self.list.setModel(self.model)
        self.body.addWidget(self.list, 1)

        # detail simbol terpilih
        box = QFrame()
        box.setObjectName("previewBox")
        bl = QHBoxLayout(box)
        bl.setContentsMargins(14, 50, 14, 10)
        bl.setSpacing(14)
        self.glyph = QLabel("—")
        self.glyph.setObjectName("glyphBig")
        self.glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.glyph.setFixedWidth(56)
        self.glyph.setFont(font_for_symbol("—", 30))
        info = QVBoxLayout()
        info.setSpacing(2)
        self.name_label = field_label("No symbol selected", "sectionTitle")
        self.code_label = field_label("Pick a symbol to see its code point.", "fieldHint", wrap=True)
        self.code_label.setFont(mono_font(10))
        info.addWidget(self.name_label)
        info.addWidget(self.code_label)
        bl.addWidget(self.glyph)
        bl.addLayout(info, 1)
        self.body.addWidget(box)

        credit = QLabel("Tested by "
                        + gradient_html("MasterThe8", ["#FF3B5C", "#FF3DB4", "#B94DFF", "#6E7BFF", "#4DA3FF"])
                        + " and tidied by "
                        + gradient_html("Ismaya Melasrana", ["#00e9ff", "#4bf388", "#a1ff00"]) + ".")
        credit.setObjectName("fieldHint")
        credit.setWordWrap(True)
        self.body.addWidget(credit)

        # footer
        self.txt_btn = make_button("Show .txt", "ghost")
        self.note = QLabel("")
        self.note.setObjectName("statusNote")
        self.close_btn = make_button("Close", "primary")
        self.footer.addWidget(self.txt_btn)
        self.footer.addWidget(self.note)
        self.footer.addStretch(1)
        self.footer.addWidget(self.close_btn)

        self.search.textChanged.connect(self._rebuild)
        self.group.idClicked.connect(self._set_category)
        self.list.clicked.connect(self._on_click)
        self.list.selectionModel().currentChanged.connect(lambda cur, _prev: self._show_detail(cur))
        self.txt_btn.clicked.connect(self.show_txt_requested.emit)
        self.close_btn.clicked.connect(self.close)
        self._note_timer.timeout.connect(lambda: self.note.setText(""))
        self._rebuild()

    # -- isi grid ------------------------------------------------------------
    def _set_category(self, index: int) -> None:
        self._category = self._names[index]
        self._rebuild()

    def _rebuild(self) -> None:
        category, query = self._category, self.search.text()

        self.model.clear()

        chars = [
            c for c in all_symbols(self._symbols, category)
            if matches(c, query)
        ]

        for ch in chars:
            self.model.appendRow(symbol_item(ch))

        self.count.setText(f"{len(chars)} symbols")

        if not chars:
            self.glyph.setText("—")
            if self._load_error:
                self.name_label.setText("Symbol list unavailable")
                self.code_label.setText(self._load_error)
            else:
                self.name_label.setText("No match")
                self.code_label.setText("Try a different search or category.")

    def _show_detail(self, index) -> None:
        ch = index.data(Qt.ItemDataRole.DisplayRole) if index.isValid() else None
        if not ch:
            return
        self.glyph.setText(ch)
        self.glyph.setFont(font_for_symbol(ch, 30))     # emoji berwarna, simbol lain monokrom
        self.name_label.setText(symbol_name(ch))
        self.code_label.setText(f"U+{ord(ch):04X}")

    # -- salin ---------------------------------------------------------------
    def _on_click(self, index) -> None:
        ch = index.data(Qt.ItemDataRole.DisplayRole)
        if not ch:
            return
        QGuiApplication.clipboard().setText(ch)
        self.note.setText(f"Copied “{ch}”")
        self._note_timer.start(1800)
        self.symbol_copied.emit(ch)
