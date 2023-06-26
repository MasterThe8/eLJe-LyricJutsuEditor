from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class AboutWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About")
        self.setFixedSize(600, 540)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.setStyleSheet("background-color:#100a21; color: #fff;")
        
        layout = QVBoxLayout()
        
        # Menambahkan logo aplikasi
        logo_label = QLabel()
        pixmap = QPixmap("img/about.png")
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedHeight(200)
        layout.addWidget(logo_label)
        
        layout.setContentsMargins(0, 0, 0, 0)

        # Menambahkan judul
        title_label = QLabel("eLJe | LyricJutsu Editor v0.1.0 (BETA)")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; color: #00FFFF; font-weight: bold;")
        title_label.setFixedHeight(20)
        layout.addWidget(title_label)

        # Menambahkan penjelasan
        description_text = QTextEdit()
        description_text.setHtml('A simple Software created by <b style="color:#FF0000;">M</b><b style="color:#FF003E;">a</b><b style="color:#FF0064;">s</b><b style="color:#FF00A2;">t</b><b style="color:#FF00D8;">e</b><b style="color:#E800FF;">r</b><b style="color:#B900FF;">T</b><b style="color:#8700FF;">h</b><b style="color:#6100FF;">e</b><b style="color:#000FFF;">8</b><br><br>This software makes it easy for Clone Hero Charter to edit lyrics from chart files (.charts) with a PlainText-based display. As well as being able to manipulate/method on lyrics which for now is usually called "Lyric Jutsu". This program displays the "Events" session section of the Chart file and Highlights the Syntax of the code. Thus, it makes it easier for users to edit and be creative in manipulating lyrics. There are several additional features in performing Lyric Jutsu such as "Symbol", "Add Jutsu", "Lyric Color (method 1)", "Lyric Color (method 2)", and "Kan2Rom".<br><br>This application has many shortcomings / bugs., and I apologize for these deficiencies. I built this application using Python GUI (QT) manually coding.')
        
        # Mengatur tinggi tetap
        description_text.setFixedHeight(260)
        font = QFont()
        font.setPointSize(12)
        description_text.setFont(font)
        description_text.setAlignment(Qt.AlignJustify)

        description_text.setReadOnly(True)
        
        layout.addWidget(description_text)
        
        # Menambahkan tombol OK
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.close)
        ok_button.setStyleSheet("background-color: #219e38;")
        ok_button.setFixedHeight(30)
        layout.addWidget(ok_button)

        self.setLayout(layout)
