import sys
import typing
from PyQt5 import QtCore
import chardet
import codecs
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

# class FindTextDialog(QDialog):
#     def __init__(self, parent=None):
#         super().__init__(parent)
        
#         self.setWindowTitle("Find Text")
        
#         self.label = QLabel("Find what:")
#         self.line_edit = QLineEdit()
        
#         self.find_button = QPushButton("Find")
#         self.find_button.setDefault(True)
#         self.find_button.setEnabled(False)
        
#         self.cancel_button = QPushButton("Cancel")
        
#         layout = QVBoxLayout()
#         layout.addWidget(self.label)
#         layout.addWidget(self.line_edit)
#         layout.addWidget(self.find_button)
#         layout.addWidget(self.cancel_button)
        
#         self.setLayout(layout)
        
#         self.line_edit.textChanged.connect(self.enable_find_button)
#         self.find_button.clicked.connect(self.accept)
#         self.cancel_button.clicked.connect(self.reject)
        
#     def enable_find_button(self, text):
#         self.find_button.setEnabled(bool(text))
        
#     def text(self):
#         return self.line_edit.text()
class FindTextDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
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
        # button_layout.addWidget(self.next_button)
        # button_layout.addWidget(self.previous_button)
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
class ReplaceTextDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Replace Text")
        
        self.find_label = QLabel("Find what:")
        self.find_line_edit = QLineEdit()
        
        self.replace_label = QLabel("Replace with:")
        self.replace_line_edit = QLineEdit()
        
        self.find_button = QPushButton("Find")
        self.find_button.setDefault(True)
        self.find_button.setEnabled(False)
        
        self.replace_button = QPushButton("Replace")
        self.replace_button.setEnabled(False)
        
        self.replace_all_button = QPushButton("Replace All")
        self.replace_all_button.setEnabled(False)
        
        self.cancel_button = QPushButton("Cancel")
        
        layout = QVBoxLayout()
        layout.addWidget(self.find_label)
        layout.addWidget(self.find_line_edit)
        layout.addWidget(self.replace_label)
        layout.addWidget(self.replace_line_edit)
        layout.addWidget(self.find_button)
        layout.addWidget(self.replace_button)
        layout.addWidget(self.replace_all_button)
        layout.addWidget(self.cancel_button)
        
        self.setLayout(layout)
        
        self.find_line_edit.textChanged.connect(self.enable_find_button)
        self.replace_line_edit.textChanged.connect(self.enable_replace_buttons)
        self.find_button.clicked.connect(self.accept)
        self.replace_button.clicked.connect(self.accept)
        self.replace_all_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
    def enable_find_button(self, text):
        self.find_button.setEnabled(bool(text))
        
    def enable_replace_buttons(self, text):
        self.replace_button.setEnabled(bool(text))
        self.replace_all_button.setEnabled(bool(text))
        
    def find_text(self):
        return self.find_line_edit.text()
    
    def replace_text(self):
        return self.replace_line_edit.text()