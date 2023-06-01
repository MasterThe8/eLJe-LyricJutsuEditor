import sys
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Custom Font Example')
        self.setGeometry(100, 100, 400, 300)

        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setGeometry(10, 10, 380, 200)

        self.input_button = QPushButton('Input Text', self)
        self.input_button.setGeometry(10, 220, 380, 30)
        self.input_button.clicked.connect(self.open_file_dialog)

    def open_file_dialog(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, 'Open Font File', '', 'Text Files (*.txt)')
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as file:
                font_text = file.read().strip()
            self.apply_custom_font(font_text)

    def apply_custom_font(self, font_text):
        font_id = QFontDatabase.addApplicationFontFromData(font_text.encode())
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if font_families:
            custom_font = QFont(font_families[0], 12)  # Ganti ukuran font yang Anda inginkan
            self.text_edit.setFont(custom_font)
            self.text_edit.setFontPointSize(12)
            print("Font Applied!")
            self.text_edit.appendPlainText('Font Applied!')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
