"""Dialog Weird Text Generator."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.dialogs.base import BaseDialog
from ui.theme import bind_pixmap
from ui.widgets.common import field_label, make_button


# ─────────────────────────────────────────────────────────────────────────────
#  Weird Text Generator
# ─────────────────────────────────────────────────────────────────────────────
class WeirdTextDialog(BaseDialog):
    """Non-modal. Emit generate_requested(text); isi hasil lewat set_results(list[str], notice, detail)."""
    generate_requested = Signal(str)
    HINT = "Click a result to copy it"

    def __init__(self, parent=None):
        super().__init__("Weird Text Generator", "Turn a line into 26 decorative alphabets.",
                         "weird", parent, modal=False)
        self.resize(560, 660)
        self.setMinimumSize(460, 500)

        self.body.addWidget(field_label("Input text"))
        row = QHBoxLayout()
        row.setSpacing(8)
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type the lyric you want to restyle…")
        self.input_box.setClearButtonEnabled(True)
        self.generate_btn = make_button("Generate", "primary", "wand")
        self.generate_btn.setEnabled(False)
        row.addWidget(self.input_box, 1)
        row.addWidget(self.generate_btn)
        self.body.addLayout(row)

        # Empty state / hasil
        empty = QWidget()
        el = QVBoxLayout(empty)
        el.setAlignment(Qt.AlignmentFlag.AlignCenter)
        glyph = QLabel()
        bind_pixmap(glyph, "setPixmap", "weird", "FAINT", 40)
        glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t1 = QLabel("No results yet")
        t1.setObjectName("emptyTitle")
        t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t2 = QLabel("Enter some text and press Generate\nto see every style at once.")
        t2.setObjectName("emptyText")
        t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for w in (glyph, t1, t2):
            el.addWidget(w)

        self.list = QListWidget()
        self.list.setWordWrap(True)
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list.setCursor(Qt.CursorShape.PointingHandCursor)
        f = QFont(self.font())
        f.setPointSize(14)
        self.list.setFont(f)

        self.stack = QStackedWidget()
        self.stack.addWidget(empty)
        self.stack.addWidget(self.list)
        self.body.addWidget(self.stack, 1)

        self._idle_hint = self.HINT                     # teks footer saat tidak ada pesan "Copied"
        self.hint = QLabel(self.HINT)
        self.hint.setObjectName("statusNote")
        self.close_btn = make_button("Close", "ghost")
        self.footer.addWidget(self.hint)
        self.footer.addStretch(1)
        self.footer.addWidget(self.close_btn)

        self.input_box.textChanged.connect(lambda t: self.generate_btn.setEnabled(bool(t.strip())))
        self.input_box.returnPressed.connect(self._generate)
        self.generate_btn.clicked.connect(self._generate)
        self.list.itemClicked.connect(self._copy_item)
        self.close_btn.clicked.connect(self.close)
        self._note_timer.timeout.connect(lambda: self.hint.setText(self._idle_hint))

    def _generate(self) -> None:
        if self.input_box.text().strip():
            self.generate_requested.emit(self.input_box.text())

    def set_results(self, texts: list[str], notice: str = "", detail: str = "") -> None:
        """``notice``: pesan singkat di footer (mis. ada file gaya yang dilewati); ``detail``: rinciannya, di tooltip."""
        self.list.clear()
        for t in texts:
            item = QListWidgetItem(t)
            item.setToolTip("Click to copy")
            self.list.addItem(item)
        self.stack.setCurrentIndex(1 if texts else 0)
        self._idle_hint = notice or self.HINT
        self.hint.setText(self._idle_hint)
        self.hint.setToolTip(detail)

    def _copy_item(self, item: QListWidgetItem) -> None:
        QGuiApplication.clipboard().setText(item.text())
        self.hint.setText("Copied to clipboard")
        self._note_timer.start(1800)
