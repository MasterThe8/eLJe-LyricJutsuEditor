import sys
import typing
from PyQt5 import QtCore
import chardet
import codecs
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class FindTextDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.setWindowTitle("Find Text")
        
        self.label = QLabel("Find what:")
        self.line_edit = QLineEdit()
        
        self.find_button = QPushButton("Find")
        self.find_button.setDefault(True)
        self.find_button.setEnabled(False)
        
        self.next_button = QPushButton("Next")
        self.previous_button = QPushButton("Previous")
        self.cancel_button = QPushButton("Cancel")
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.find_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        self.line_edit.textChanged.connect(self.enable_find_button)
        self.find_button.clicked.connect(self.accept)
        self.next_button.clicked.connect(self.next_find)
        self.previous_button.clicked.connect(self.previous_find)
        self.cancel_button.clicked.connect(self.reject)
        
        self.search_direction = QTextDocument.FindFlag(0)
        
    def enable_find_button(self, text):
        self.find_button.setEnabled(bool(text))
        
    def text(self):
        return self.line_edit.text()
    
    def next_find(self):
        self.search_direction = QTextDocument.FindFlag(0)
        self.accept()
        
    def previous_find(self):
        self.search_direction = QTextDocument.FindBackward
        self.accept()