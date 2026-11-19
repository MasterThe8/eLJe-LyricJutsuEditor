"""Dialog Setting › Appearance (tema aplikasi)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QLabel

from ui.dialogs.base import BaseDialog
from ui.theme import DEFAULT_THEME_ID, ThemeManager
from ui.widgets.common import field_label, make_button


class AppearanceDialog(BaseDialog):
    """Pilih tema aplikasi. Perubahan langsung diterapkan dan disimpan (tanpa tombol Apply)."""

    def __init__(self, manager: ThemeManager, parent=None):
        super().__init__("Appearance", "Choose how the application looks.", "display", parent)
        self.setMinimumWidth(460)
        self._manager = manager

        self.body.addWidget(field_label("Application Theme"))
        self.combo = QComboBox()
        for t in manager.available_themes():
            self.combo.addItem(t["name"], t["id"])
            self.combo.setItemData(self.combo.count() - 1, t["description"], Qt.ItemDataRole.ToolTipRole)
        self.body.addWidget(self.combo)

        self.description = field_label("", "fieldHint")
        self.description.setWordWrap(True)
        self.body.addWidget(self.description)
        self.body.addSpacing(6)
        self.body.addWidget(field_label("The selected theme is applied immediately. "
                                        "Changes are saved automatically.", "fieldHint"))
        self.body.addStretch(1)

        self.reset_btn = make_button("Set Default", "ghost", "reset")
        self.note = QLabel("")
        self.note.setObjectName("statusNote")
        self.close_btn = make_button("Close", "primary")
        self.close_btn.setDefault(True)
        self.footer.addWidget(self.reset_btn)
        self.footer.addWidget(self.note)
        self.footer.addStretch(1)
        self.footer.addWidget(self.close_btn)

        self._select(manager.current_theme)
        self.combo.currentIndexChanged.connect(self._on_changed)
        self.reset_btn.clicked.connect(lambda: self._select(DEFAULT_THEME_ID, apply=True))
        self.close_btn.clicked.connect(self.accept)
        self._note_timer.timeout.connect(lambda: self.note.setText(""))

    def _select(self, theme_id: str, apply: bool = False) -> None:
        idx = self.combo.findData(theme_id)
        if idx < 0:
            idx = self.combo.findData(DEFAULT_THEME_ID)
        self.combo.blockSignals(True)
        self.combo.setCurrentIndex(idx)
        self.combo.blockSignals(False)
        self._show_description()
        if apply:
            self._on_changed(idx)

    def _show_description(self) -> None:
        theme_id = self.combo.currentData()
        for t in self._manager.available_themes():
            if t["id"] == theme_id:
                self.description.setText(t["description"])
                return

    def _on_changed(self, index: int) -> None:
        theme_id = self.combo.itemData(index)
        if self._manager.set_theme(theme_id):
            self._show_description()
            self.note.setText("Saved")
        else:                                           # tidak seharusnya terjadi; pulihkan pilihan
            self._select(self._manager.current_theme)
            self.note.setText("Theme not available")
        self._note_timer.start(2000)
