import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QTextEdit, QPlainTextEdit
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Tabbed Text Editor")
        self.setGeometry(300, 300, 400, 300)

        # Membuat widget utama dan tata letak utama
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # Membuat QTabWidget
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(PlainTextTab(), "Plain Text")
        self.tab_widget.addTab(RichTextTab(), "Rich Text")

        # Menambahkan QTabWidget ke tata letak utama
        layout.addWidget(self.tab_widget)


class PlainTextTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        self.text_edit = QPlainTextEdit()
        layout.addWidget(self.text_edit)

        # Menghubungkan slot textChanged ke peristiwa textChanged
        self.text_edit.textChanged.connect(self.updateRichText)

    def updateRichText(self):
        # Mendapatkan teks dari PlainTextTab
        text = self.text_edit.toPlainText()

        # Mendapatkan objek RichTextTab dari tab lainnya
        main_window = self.window()
        rich_text_tab = main_window.tab_widget.widget(1)

        # Mengatur teks pada RichTextTab
        rich_text_tab.text_edit.setPlainText(text)


class RichTextTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(True)
        layout.addWidget(self.text_edit)

        # Menghubungkan slot textChanged ke peristiwa editingFinished
        self.text_edit.textChanged.connect(self.updatePlainText)

    def updatePlainText(self):
        # Mendapatkan teks dari RichTextTab
        text = self.text_edit.toPlainText()

        # Mendapatkan objek PlainTextTab dari tab lainnya
        main_window = self.window()
        plain_text_tab = main_window.tab_widget.widget(0)

        # Mengatur teks pada PlainTextTab
        plain_text_tab.text_edit.setPlainText(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
