"""Kerangka dialog Setting (Apply / Set Default / Close)."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel

from ui.dialogs.base import BaseDialog
from ui.widgets.common import make_button


# ─────────────────────────────────────────────────────────────────────────────
#  Kerangka dialog Setting  (Set Default · Close · Apply)
# ─────────────────────────────────────────────────────────────────────────────
class SettingsDialog(BaseDialog):
    applied = Signal(dict)

    def __init__(self, title: str, subtitle: str, icon_name: str, parent=None):
        super().__init__(title, subtitle, icon_name, parent)
        self.reset_btn = make_button("Set Default", "ghost", "reset")
        self.note = QLabel("")
        self.note.setObjectName("statusNote")
        self.close_btn = make_button("Close", "ghost")
        self.apply_btn = make_button("Apply", "primary")
        self.apply_btn.setDefault(True)
        self.footer.addWidget(self.reset_btn)
        self.footer.addWidget(self.note)
        self.footer.addStretch(1)
        self.footer.addWidget(self.close_btn)
        self.footer.addWidget(self.apply_btn)

        self.reset_btn.clicked.connect(self._on_reset)
        self.apply_btn.clicked.connect(self._on_apply)
        self.close_btn.clicked.connect(self.close)
        self._note_timer.timeout.connect(lambda: self.note.setText(""))

    # subclass mengimplementasikan tiga hal ini
    def values(self) -> dict:
        raise NotImplementedError

    def set_values(self, data: dict) -> None:
        raise NotImplementedError

    def defaults(self) -> dict:
        raise NotImplementedError

    def _flash(self, message: str) -> None:
        self.note.setText(message)
        self._note_timer.start(2000)

    def _on_apply(self) -> None:
        self.applied.emit(self.values())
        self._flash("Applied")

    def _on_reset(self) -> None:
        self.set_values(self.defaults())
        self.applied.emit(self.values())            # sama seperti aslinya: default langsung berlaku
        self._flash("Defaults restored")
