"""Panel kanan: TempText dan Symbol Picker."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QListView,
    QPlainTextEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.text_tools.symbols import all_symbols
from services.text_assets import AssetError, read_symbols
from ui.widgets.common import panel_header
from ui.widgets.symbol_grid import configure_symbol_view, symbol_item


# ─────────────────────────────────────────────────────────────────────────────
#  Panel kanan: TempText + Symbol Picker
# ─────────────────────────────────────────────────────────────────────────────
class SidePanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dockRight")
        self.setMinimumWidth(260)

        # TempText
        self.temp_text = QPlainTextEdit()
        self.temp_text.setObjectName("tempText")
        self.temp_text.setPlaceholderText("Scratch space for lines you want to keep nearby…")
        self.temp_text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        top = QWidget()
        tl = QVBoxLayout(top)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(0)
        tl.addWidget(panel_header("TempText"))
        box = QWidget()
        bl = QVBoxLayout(box)
        bl.setContentsMargins(14, 0, 14, 12)
        bl.addWidget(self.temp_text)
        tl.addWidget(box, 1)

        # Symbol picker — data dari assets/symbols/CH_Lyric_Symbols.txt (sama dengan jendela Get Symbol)
        try:
            self._symbols = read_symbols()
            load_error = ""
        except AssetError as exc:
            self._symbols = {}
            load_error = str(exc)
        self.category = QComboBox()
        self.category.addItems(["All"] + list(self._symbols))
        self.category.setCursor(Qt.CursorShape.PointingHandCursor)
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
        self.list.setCursor(Qt.CursorShape.PointingHandCursor)
        self.model = QStandardItemModel(self.list)
        self.list.setModel(self.model)
        if load_error:
            self.list.setToolTip(load_error)            # daftar kosong: alasannya terlihat saat kursor di atasnya

        bottom = QWidget()
        bt = QVBoxLayout(bottom)
        bt.setContentsMargins(0, 0, 0, 0)
        bt.setSpacing(0)
        bt.addWidget(panel_header("Symbol Picker", self.category))
        grid = QWidget()
        gl = QVBoxLayout(grid)
        gl.setContentsMargins(10, 0, 10, 10)
        gl.addWidget(self.list)
        bt.addWidget(grid, 1)

        split = QSplitter(Qt.Orientation.Vertical)
        split.setChildrenCollapsible(False)
        split.setHandleWidth(7)
        split.addWidget(top)
        split.addWidget(bottom)
        split.setStretchFactor(0, 2)
        split.setStretchFactor(1, 3)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(split)

        self.category.currentTextChanged.connect(self._fill)
        self._fill("All")

    def _fill(self, name: str) -> None:
        self.model.clear()
        for ch in all_symbols(self._symbols, name):
            self.model.appendRow(symbol_item(ch))
