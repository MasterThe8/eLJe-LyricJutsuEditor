"""Dialog Select Color."""
from __future__ import annotations

from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QColor, QGuiApplication, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ui.dialogs.base import BaseDialog
from services.defaults import DEFAULT_PICKER_COLOR
from ui.theme import Theme, mono_font
from ui.widgets.color_widgets import HueSlider, PreviewSwatch, SVPicker
from ui.widgets.common import add_line_edit_icon, field_label, make_button

# ─────────────────────────────────────────────────────────────────────────────
#  Select Color  (pengganti QColorDialog — dipakai Color Picker & Highlight)
# ─────────────────────────────────────────────────────────────────────────────
COLOR_PRESETS = [
    "#FF00FF", "#F5FF5E", "#00FF7F", "#03FCF4", "#FF003E", "#B900FF", "#000FFF", "#1BEEF5",
    "#FFFFFF", "#FF5E9C", "#FFA94D", "#FFE066", "#69DB7C", "#4DABF7", "#9775FA", "#868E96",
]


class ColorDialog(BaseDialog):
    """Pemilih warna bertema. Pakai ColorDialog.get_color(initial, parent) →
    QColor (tidak valid bila dibatalkan)."""

    def __init__(self, initial: QColor | None = None, parent=None, title: str = "Select Color"):
        super().__init__(title, "Choose a color for lyrics and highlights.", "picker", parent)
        self.setMinimumWidth(620)
        self._initial = QColor(initial) if initial is not None and initial.isValid() else QColor(DEFAULT_PICKER_COLOR)
        self._h = max(0, self._initial.hsvHue())
        self._s, self._v = 255, 255
        self._updating = False
        self._result: QColor | None = None

        # ── kiri: SV + hue + presets ──
        self.sv = SVPicker()
        self.hue = HueSlider()
        left = QVBoxLayout()
        left.setSpacing(10)
        left.addWidget(self.sv, 1)
        left.addWidget(self.hue)
        left.addSpacing(4)
        left.addWidget(field_label("Presets"))
        grid = QGridLayout()
        grid.setSpacing(6)
        for i, hex_ in enumerate(COLOR_PRESETS):
            b = QPushButton()
            b.setFixedSize(26, 26)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setToolTip(hex_)
            b.setStyleSheet(
                f"QPushButton {{ background: {hex_}; border: 1px solid {Theme.BORDER_HI}; border-radius: 7px; padding: 0; }}"
                f"QPushButton:hover {{ border: 2px solid {Theme.ACCENT}; }}")
            b.clicked.connect(lambda _=False, c=hex_: self._set_color(QColor(c)))
            grid.addWidget(b, i // 8, i % 8)
        grid.setColumnStretch(8, 1)
        left.addLayout(grid)

        # ── kanan: preview, hex, rgb ──
        self.preview = PreviewSwatch(self._initial)
        caps = QHBoxLayout()
        caps.addWidget(field_label("Current", "fieldHint"))
        caps.addStretch(1)
        caps.addWidget(field_label("New", "fieldHint"))

        self.hex = QLineEdit()
        self.hex.setFont(mono_font(11))
        self.hex.setMaxLength(7)
        self.hex.setValidator(QRegularExpressionValidator(QRegularExpression(r"#?[0-9A-Fa-f]{0,6}")))
        copy_action = add_line_edit_icon(self.hex, "copy", QLineEdit.ActionPosition.TrailingPosition)
        copy_action.setToolTip("Copy hex")
        copy_action.triggered.connect(self._copy_hex)

        self.spins = []
        rgb = QGridLayout()
        rgb.setHorizontalSpacing(8)
        rgb.setVerticalSpacing(8)
        for i, name in enumerate("RGB"):
            sp = QSpinBox()
            sp.setRange(0, 255)
            sp.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            sp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sp.valueChanged.connect(self._on_rgb)
            self.spins.append(sp)
            rgb.addWidget(field_label(name), 0, i, Qt.AlignmentFlag.AlignHCenter)
            rgb.addWidget(sp, 1, i)

        right = QVBoxLayout()
        right.setSpacing(8)
        right.addWidget(self.preview)
        right.addLayout(caps)
        right.addSpacing(6)
        right.addWidget(field_label("Hex"))
        right.addWidget(self.hex)
        right.addSpacing(4)
        right.addLayout(rgb)
        right.addStretch(1)
        right_w = QWidget()
        right_w.setLayout(right)
        right_w.setFixedWidth(210)

        row = QHBoxLayout()
        row.setSpacing(20)
        row.addLayout(left, 1)
        row.addWidget(right_w)
        self.body.addLayout(row, 1)

        self.cancel_btn = make_button("Cancel", "ghost")
        self.select_btn = make_button("Select", "primary", "check")
        self.select_btn.setDefault(True)
        self.footer.addStretch(1)
        self.footer.addWidget(self.cancel_btn)
        self.footer.addWidget(self.select_btn)
        self.cancel_btn.clicked.connect(self.reject)
        self.select_btn.clicked.connect(self._accept)

        self.sv.changed.connect(self._on_sv)
        self.hue.changed.connect(self._on_hue)
        self.hex.textEdited.connect(self._on_hex)
        self._set_color(self._initial)

    # -- state ------------------------------------------------------------
    def _current(self) -> QColor:
        return QColor.fromHsv(self._h, self._s, self._v)

    def _set_color(self, c: QColor, keep_hex: bool = False) -> None:
        self._updating = True
        if c.hsvHue() >= 0:                      # abu-abu → hue tidak terdefinisi, pertahankan
            self._h = c.hsvHue()
        self._s, self._v = c.hsvSaturation(), c.value()
        for sp, val in zip(self.spins, (c.red(), c.green(), c.blue())):
            sp.setValue(val)
        self.sv.set_hsv(self._h, self._s, self._v)
        self.hue.set_hue(self._h)
        if not keep_hex:
            self.hex.setText(c.name().upper())
        self.preview.set_new(c)
        self._updating = False

    def _on_sv(self, s: int, v: int) -> None:
        self._set_color(QColor.fromHsv(self._h, s, v))

    def _on_hue(self, h: int) -> None:
        self._set_color(QColor.fromHsv(h, self._s, self._v))

    def _on_rgb(self) -> None:
        if not self._updating:
            self._set_color(QColor(*(sp.value() for sp in self.spins)))

    def _on_hex(self, text: str) -> None:
        t = text.lstrip("#")
        if len(t) == 6:
            self._set_color(QColor("#" + t), keep_hex=True)

    def _copy_hex(self) -> None:
        QGuiApplication.clipboard().setText(self._current().name().upper())

    def _accept(self) -> None:
        self._result = self._current()
        self.accept()

    @staticmethod
    def get_color(initial: QColor | None = None, parent=None, title: str = "Select Color") -> QColor:
        dlg = ColorDialog(initial, parent, title)
        dlg.exec()
        return QColor(dlg._result) if dlg._result is not None else QColor()
