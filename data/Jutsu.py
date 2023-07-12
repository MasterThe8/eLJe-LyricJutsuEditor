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
        self.center_window(300,500)
        self.resize(300, 250)
        
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        icon = QIcon("img/addjutsu.png")
        self.setWindowIcon(icon)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        image_label = QLabel()
        pixmap = QPixmap("img/addjutsu.png")
        image_label.setPixmap(pixmap.scaled(280,150))
        layout.addWidget(image_label)
        
        self.comboBox = QComboBox()
        self.comboBox.addItems(['No SlideUp Transition', 'Hide Next Phrase', 'Fake Next Phrase'])
        self.comboBox.currentTextChanged.connect(self.handle_combobox_changed)
        self.lineEdit = QLineEdit()
        self.positionEdit = QLineEdit()
        self.fakelyric = QLineEdit()
        
        self.positionLabel = QLabel('Input Position :')
        self.jutsuLabel = QLabel('Pilih Jutsu')
        self.textLabel = QLabel('Input Lyric :')
        self.textfakeLabel = QLabel('Input Fake Lyric :')
        
        self.okButton = QPushButton('OK')
        self.okButton.clicked.connect(self.accept)
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.reject)
        
        # Tambahkan garis pemisah horizontal
        line = QFrame()
        line2 = QFrame()
        line3 = QFrame()
        line.setFrameShape(QFrame.HLine)
        line2.setFrameShape(QFrame.HLine)
        line3.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line2.setFrameShadow(QFrame.Sunken)
        line3.setFrameShadow(QFrame.Sunken)
        
        layout.addWidget(self.positionLabel)
        layout.addWidget(self.positionEdit)
        layout.addWidget(line)
        layout.addWidget(self.jutsuLabel)
        layout.addWidget(self.comboBox)
        layout.addWidget(line2)
        layout.addWidget(self.textLabel)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.textfakeLabel)
        layout.addWidget(self.fakelyric)
        layout.addWidget(line3)
        layout.addWidget(self.okButton)
        layout.addWidget(self.cancelButton)
        self.setLayout(layout)
        
        self.textfakeLabel.setDisabled(True)
        self.fakelyric.setDisabled(True)
        
    def center_window(self, width, height):
        screen = QDesktopWidget().screenGeometry()
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.setGeometry(x, y, width, height)
    
    def focusOutEvent(self, event):
        self.activateWindow()
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.show()
        super().focusOutEvent(event)
        
    def handle_combobox_changed(self, text):
        if text == 'Fake Next Phrase':
            self.textfakeLabel.setDisabled(False)
            self.fakelyric.setDisabled(False)
        else:
            self.textfakeLabel.setDisabled(True)
            self.fakelyric.setDisabled(True)
            
    def accept(self):
        # script_value = self.main_window.getScript()
        # script_value = script_value.splitlines()
        
        jutsuSelected = self.comboBox.currentText()
        positionInput = self.positionEdit.text()
        position = None
        if positionInput.isdigit():
            position = int(positionInput)
        else:
            QMessageBox.critical(self, "Error", "Position must be filled correctly!")
            self.show()
        if position is not None:
            lyricInput = self.lineEdit.text()
            fakeLyric = self.fakelyric.text()
            
            jutsuInput = ""
            jutsuName = ['No SlideUp Transition', 'Hide Next Phrase', 'Fake Next Phrase']
            
            if jutsuSelected == jutsuName[0]:
                line1 = str(position) + " = E \"lyric <i></i>\""
                line2 = str(position+1) + " = E \"phrase_start\""
                line3 = str(position+2) + " = E \"lyric "+lyricInput+"\""
                jutsuInput = line1 + '\n' + line2 + '\n' + line3
                
            elif jutsuSelected == jutsuName[1]:
                line1 = str(position) + " = E \"lyric <i></i>\""
                line2 = str(position+1) + " = E \"phrase_start\""
                line3 = str(position+2) + " = E \"lyric <i>_</i>\""
                line4 = str(position+3) + " = E \"phrase_start\""
                line5 = str(position+4) + " = E \"lyric "+lyricInput+"\""
                jutsuInput = line1 + '\n' + line2 + '\n' + line3 + '\n' + line4 + '\n' + line5

            elif jutsuSelected == jutsuName[2]:
                line1 = str(position) + " = E \"lyric <i></i>\""
                line2 = str(position+1) + " = E \"phrase_start\""
                line3 = str(position+2) + " = E \"lyric " + fakeLyric + "\""
                line4 = str(position+3) + " = E \"phrase_start\""
                line5 = str(position+4) + " = E \"lyric "+lyricInput+"\""
                jutsuInput = line1 + '\n' + line2 + '\n' + line3 + '\n' + line4 + '\n' + line5

            cursor = self.parent().plainTextEdit.textCursor()
            cursor.insertText(str(jutsuInput))
            self.parent().plainTextEdit.setTextCursor(cursor)
            
            super(AddJutsu, self).accept()
    
    def reject(self):
        super(AddJutsu, self).reject()