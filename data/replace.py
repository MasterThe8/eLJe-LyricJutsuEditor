from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class Replace(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Replace")
        self.setModal(True)
        
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        self.label_original = QLabel("Text:")
        self.line_edit_original = QLineEdit()
        self.label_replace = QLabel("Replace with:")
        self.line_edit_replace = QLineEdit()
        self.button_replace_all = QPushButton("Replace All")
        self.button_replace_all.clicked.connect(self.replace_all)
        self.button_cancel = QPushButton("Cancel")
        self.button_cancel.clicked.connect(self.close)

        layout.addWidget(self.label_original)
        layout.addWidget(self.line_edit_original)
        layout.addWidget(self.label_replace)
        layout.addWidget(self.line_edit_replace)
        layout.addWidget(self.button_replace_all)
        layout.addWidget(self.button_cancel)

    def replace_all(self):
        original_text = self.line_edit_original.text()
        replacement_text = self.line_edit_replace.text()
        if original_text and replacement_text:
            script = self.main_window.getScript()
            replaced_script = script.replace(original_text, replacement_text)
            
            scroll_bar = self.main_window.plainTextEdit.verticalScrollBar()
            scroll_pos = scroll_bar.value()
            self.main_window.plainTextEdit.setPlainText(replaced_script)
            scroll_bar.setValue(scroll_pos)
            shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
            shortcut_undo.activated.connect(self.undo_text)
            shortcut_redo = QShortcut(QKeySequence("Ctrl+Y"), self)
            shortcut_redo.activated.connect(self.redo_text)
        self.close()
    def reject(self):
        super(Replace, self).reject()
    def undo_text(self):
        self.main_window.plainTextEdit.undo()  
    def redo_text(self):
        self.main_window.plainTextEdit.redo() 