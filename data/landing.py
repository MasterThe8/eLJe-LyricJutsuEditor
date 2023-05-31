from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class LandingPageWindow(QMainWindow):
    def __init__(self, main_window):
        super().__init__()
        
        self.main_window = main_window
        self.setWindowTitle("Landing Page")
        self.center_window(800,400)
        
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        central_widget.setLayout(layout)
        
        label1 = QLabel("eLJe | LyricJutsu Chart Editor")
        label1.setFont(QFont("Arial", 32))
        layout.addWidget(label1)

        label2 = QLabel("MasterThe8")
        label2.setFont(QFont("Arial", 18))
        layout.addWidget(label2)

        button = QPushButton("Open Chart File")
        button.clicked.connect(self.open_main_window)
        layout.addWidget(button)

        with open('style/landing.css', 'r') as f:
            style_sheet = f.read()
        
        self.setStyleSheet(style_sheet)

    def center_window(self, width, height):
        screen = QDesktopWidget().screenGeometry()
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.setGeometry(x, y, width, height)

    def open_main_window(self):
        self.close()
        self.main_window.open_file()
        self.main_window.setEnabled(True)