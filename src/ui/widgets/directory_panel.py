"""Panel kiri: daftar file .chart."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDir, QSize, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileSystemModel,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from ui.theme import Theme, bind_pixmap, icon
from ui.widgets.common import panel_header, tool_button


# ─────────────────────────────────────────────────────────────────────────────
#  Model file: hanya ikon yang diganti (aslinya override header/data juga)
# ─────────────────────────────────────────────────────────────────────────────
class ChartFileModel(QFileSystemModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DecorationRole and index.column() == 0:
            # diselesaikan saat dipanggil (cache ikon di icons.py) → selalu sesuai tema aktif
            if self.isDir(index):
                return icon("folder_big", Theme.DIM, Theme.DIM)
            return icon("chart_file", Theme.ACCENT, Theme.ACCENT)
        return super().data(index, role)


class DirectoryPanel(QFrame):
    """Header + tree .chart, dengan empty state bila folder kosong."""

    def __init__(self, root: str, parent=None):
        super().__init__(parent)
        self.setObjectName("dockLeft")
        self.setMinimumWidth(220)

        self.hint = QLabel()
        self.hint.setObjectName("panelHint")
        self.browse_btn = tool_button("open", "Choose song chart folder")

        self.model = ChartFileModel(self)
        self.model.setFilter(QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)
        self.model.setNameFilters(["*.chart"])
        self.model.setNameFilterDisables(False)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setIndentation(16)
        self.tree.setIconSize(QSize(16, 16))
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        for col in range(1, self.model.columnCount()):
            self.tree.setColumnHidden(col, True)

        self.choose_btn = QPushButton("Choose folder")
        self.choose_btn.setObjectName("primary")
        self.choose_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.empty = self._build_empty_state()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.empty)
        self.stack.addWidget(self.tree)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 6)
        lay.setSpacing(0)
        lay.addWidget(panel_header("Song Chart Directory", self.browse_btn))
        hint_row = QWidget()
        hl = QHBoxLayout(hint_row)
        hl.setContentsMargins(16, 0, 12, 8)
        hl.addWidget(self.hint)
        lay.addWidget(hint_row)
        lay.addWidget(self.stack, 1)

        self.model.directoryLoaded.connect(self._on_loaded)
        self.set_root(root)

    def _build_empty_state(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(24, 0, 24, 40)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        glyph = QLabel()
        bind_pixmap(glyph, "setPixmap", "folder_big", "FAINT", 40)
        glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("No chart files here")
        title.setObjectName("emptyTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text = QLabel("Pick the folder that holds your\n.chart files to list them.")
        text.setObjectName("emptyText")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(glyph)
        lay.addSpacing(6)
        lay.addWidget(title)
        lay.addWidget(text)
        lay.addSpacing(10)
        lay.addWidget(self.choose_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        return w

    def set_root(self, path: str) -> None:
        self._root = Path(path)
        self.model.setRootPath(path)
        self.tree.setRootIndex(self.model.index(path))
        self.hint.setText(self._root.name or str(self._root))
        self.hint.setToolTip(str(self._root))
        self._refresh_state()

    def _on_loaded(self, loaded_path: str) -> None:
        if Path(loaded_path) == self._root:
            self._refresh_state()

    def _refresh_state(self) -> None:
        has_rows = self.model.rowCount(self.model.index(str(self._root))) > 0
        self.stack.setCurrentIndex(1 if has_rows else 0)
