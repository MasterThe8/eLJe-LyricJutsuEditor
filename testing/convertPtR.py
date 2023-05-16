import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QFont

class HTMLtoRichTextConverter(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("HTML to Rich Text Converter")
        self.setGeometry(100, 100, 800, 600)

        self.plainTextEdit = QTextEdit(self)
        self.plainTextEdit.setGeometry(10, 10, 780, 500)

        self.convertButton = QPushButton("Convert", self)
        self.convertButton.setGeometry(10, 520, 100, 30)
        self.convertButton.clicked.connect(self.convertPlainTextToRichText)

    def convertPlainTextToRichText(self):
        plainText = self.plainTextEdit.toPlainText()
        rich_text = self.convertHTMLToRichText(plainText)
        self.plainTextEdit.clear()
        self.plainTextEdit.setHtml(rich_text)

    def convertHTMLToRichText(self, plainText):
        rich_text = ""

        font = self.plainTextEdit.currentFont()
        default_font_size = font.pointSize()

        # Buat format teks tebal menggunakan HTML tag <b>
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Bold)

        # Cari tag HTML <b> dan </b> dalam teks
        start_index = plainText.find("<b>")
        end_index = plainText.find("</b>")

        while start_index != -1 and end_index != -1:
            # Tambahkan teks sebelum tag <b> ke rich text
            rich_text += plainText[:start_index]

            # Tambahkan teks tebal ke rich text
            bold_text = plainText[start_index + 3 : end_index]
            rich_text += "<span style='font-weight: bold;'>{}</span>".format(bold_text)

            # Potong teks yang sudah ditambahkan dari plain text
            plainText = plainText[end_index + 4:]

            # Cari tag HTML <b> dan </b> selanjutnya dalam teks
            start_index = plainText.find("<b>")
            end_index = plainText.find("</b>")

        # Tambahkan sisa teks setelah tag terakhir ke rich text
        rich_text += plainText

        return rich_text

if __name__ == "__main__":
    app = QApplication(sys.argv)
    converter = HTMLtoRichTextConverter()
    converter.show()
    sys.exit(app.exec_())
