import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QTextEdit, QPlainTextEdit, QWidget
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        centralWidget = QWidget(self)
        layout = QVBoxLayout(centralWidget)

        self.textEdit = QTextEdit()
        self.textEdit.textChanged.connect(self.updatePlainText)

        self.plainTextEdit = QPlainTextEdit()
        self.plainTextEdit.setReadOnly(True)

        layout.addWidget(self.textEdit)
        layout.addWidget(self.plainTextEdit)

        self.setCentralWidget(centralWidget)
        self.setWindowTitle("RichText and PlainText Example")
        self.show()

    def updatePlainText(self):
        richText = self.textEdit.toPlainText()
        self.plainTextEdit.setPlainText(richText)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    sys.exit(app.exec_())
