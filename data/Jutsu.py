import sys
import typing
from PyQt5 import QtCore
import chardet
import codecs
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class AddJutsu(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Add Lyric Jutsu")
        self.setGeometry(420, 240, 300, 300)
        self.resize(400, 200)
        
        layout = QVBoxLayout()
        self.comboBox = QComboBox()
        self.comboBox.addItems(['No SlideUp Transition', 'Hide Next Phrase'])
        self.lineEdit = QLineEdit()
        self.positionEdit = QLineEdit()
        
        self.positionLabel = QLabel('Input Position :')
        self.jutsuLabel = QLabel('Pilih Jutsu')
        self.textLabel = QLabel('Input Lyric :')
        
        self.okButton = QPushButton('OK')
        self.okButton.clicked.connect(self.accept)
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.reject)
        
        layout.addWidget(self.positionLabel)
        layout.addWidget(self.positionEdit)
        layout.addWidget(self.jutsuLabel)
        layout.addWidget(self.comboBox)
        layout.addWidget(self.textLabel)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.okButton)
        layout.addWidget(self.cancelButton)
        self.setLayout(layout)
    
    # def insertTextAtCursor(plaintext, text):
    # cursor = plaintext.textCursor()
    # cursor.insertText(text)
    # plaintext.setTextCursor(cursor)
    def focusOutEvent(self, event):
        self.activateWindow()
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.show()
        super().focusOutEvent(event)
        
    def accept(self):
        # index = self.comboBox.currentIndex()
        # jutsuSelected = self.comboBox.itemText(index)
        jutsuSelected = self.comboBox.currentText()
        positionInput = self.positionEdit.text()
        position = int(positionInput)
        lyricInput = self.lineEdit.text()
        
        jutsuInput = ""
        
        if jutsuSelected == 'No SlideUp Transition':
            line1 = str(position) + " = E \"lyric _\""
            line2 = str(position+1) + " = E \"phrase_start\""
            line3 = str(position+2) + " = E \"lyric "+lyricInput+"\""
            jutsuInput = line1 + '\n' + line2 + '\n' + line3
            
        elif jutsuSelected == 'Hide Next Phrase':
            line1 = str(position) + " = E \"lyric _\""
            line2 = str(position+1) + " = E \"phrase_start\""
            line3 = str(position+2) + " = E \"lyric _\""
            line4 = str(position+3) + " = E \"phrase_start\""
            line5 = str(position+4) + " = E \"lyric "+lyricInput+"\""
            jutsuInput = line1 + '\n' + line2 + '\n' + line3 + '\n' + line4 + '\n' + line5
        
        cursor = self.parent().plainTextEdit.textCursor()
        cursor.insertText(str(jutsuInput))
        self.parent().plainTextEdit.setTextCursor(cursor)
        
        super(AddJutsu, self).accept()
    
    def reject(self):
        super(AddJutsu, self).reject()