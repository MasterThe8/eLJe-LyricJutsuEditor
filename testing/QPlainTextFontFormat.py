import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QPushButton, QColorDialog
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QFont


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setGeometry(50, 50, 200, 200)

        self.button_bold = QPushButton("Bold", self)
        self.button_bold.setGeometry(50, 260, 60, 30)
        self.button_bold.clicked.connect(self.set_bold)

        self.button_italic = QPushButton("Italic", self)
        self.button_italic.setGeometry(120, 260, 60, 30)
        self.button_italic.clicked.connect(self.set_italic)

        self.button_color = QPushButton("Color", self)
        self.button_color.setGeometry(190, 260, 60, 30)
        self.button_color.clicked.connect(self.set_color)

    def set_bold(self):
        cursor = self.text_edit.textCursor()
        format = cursor.charFormat()
        font = format.font()
        font.setBold(not font.bold())
        format.setFont(font)
        cursor.setCharFormat(format)
        self.text_edit.setFocus()

    def set_italic(self):
        cursor = self.text_edit.textCursor()
        format = cursor.charFormat()
        font = format.font()
        font.setItalic(not font.italic())
        format.setFont(font)
        cursor.setCharFormat(format)
        self.text_edit.setFocus()

    def set_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            cursor = self.text_edit.textCursor()
            format = cursor.charFormat()
            format.setForeground(color)
            cursor.setCharFormat(format)
            self.text_edit.setFocus()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.setGeometry(300, 300, 300, 350)
    main_window.show()
    sys.exit(app.exec_())
