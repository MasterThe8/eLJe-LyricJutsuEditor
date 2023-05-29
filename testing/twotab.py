import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QTextEdit
from PyQt5.QtCore import QObject, pyqtSignal


class TextEditWrapper(QObject):
    textChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.text_edit = QTextEdit()
        self.text_edit.textChanged.connect(self.emitTextChanged)

    def emitTextChanged(self):
        text = self.text_edit.toPlainText()
        self.textChanged.emit(text)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Tab TextEdit Example")

        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        self.tab1 = TextEditWrapper()
        self.tab2 = TextEditWrapper()

        self.tab1.textChanged.connect(self.update_tab2_text)
        self.tab2.textChanged.connect(self.update_tab1_text)

        self.tab_widget.addTab(self.tab1.text_edit, "Tab 1")
        self.tab_widget.addTab(self.tab2.text_edit, "Tab 2")

    def update_tab2_text(self, text):
        self.tab2.text_edit.setPlainText(text)

    def update_tab1_text(self, text):
        self.tab1.text_edit.setPlainText(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
