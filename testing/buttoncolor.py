import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QColorDialog
from PyQt5.QtGui import QColor, QTextCursor


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Text Editor")
        self.setGeometry(100, 100, 500, 400)

        self.text_edit = QTextEdit(self)
        self.text_edit.setGeometry(10, 10, 480, 300)

        self.color_button = QPushButton('Ubah Warna Teks', self)
        self.color_button.setGeometry(10, 320, 120, 30)
        self.color_button.clicked.connect(self.change_selected_text_color)

    def change_selected_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            text_cursor = self.text_edit.textCursor()
            selected_text = text_cursor.selectedText()

            formatted_text = '<span style="color: {};">{}</span>'.format(color.name(), selected_text)
            html = self.text_edit.toHtml()
            modified_html = html.replace(selected_text, formatted_text)
            self.text_edit.setHtml(modified_html)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = TextEditor()
    editor.show()
    sys.exit(app.exec_())
