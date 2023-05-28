import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.textEdit = QTextEdit()
        self.setCentralWidget(self.textEdit)

        self.find_action = QAction("Find", self)
        self.find_action.setShortcut(QKeySequence.Find)
        self.find_action.triggered.connect(self.show_find_dialog)
        self.addAction(self.find_action)

        self.find_dialog = FindDialog(self)
        self.find_dialog.find_next.connect(self.find_next)
        self.find_dialog.find_previous.connect(self.find_previous)

        self.show()

    def show_find_dialog(self):
        self.find_dialog.show()

    def find_next(self, text):
        cursor = self.textEdit.textCursor()
        cursor = self.textEdit.document().find(text, cursor)

        if cursor.isNull():
            self.textEdit.setTextCursor(self.textEdit.textCursor())
        else:
            self.textEdit.setTextCursor(cursor)

    def find_previous(self, text):
        cursor = self.textEdit.textCursor()
        backwards_cursor = QTextCursor(cursor)
        backwards_cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)

        cursor = self.textEdit.document().find(text, backwards_cursor)

        if cursor.isNull():
            self.textEdit.setTextCursor(self.textEdit.textCursor())
        else:
            self.textEdit.setTextCursor(cursor)

class FindDialog(QDialog):
    find_next = pyqtSignal(str)
    find_previous = pyqtSignal(str)

    def __init__(self, parent=None):
        super(FindDialog, self).__init__(parent)
        self.setWindowTitle("Find")
        self.setModal(True)

        self.find_field = QLineEdit()
        self.next_button = QPushButton("Next")
        self.prev_button = QPushButton("Previous")

        self.next_button.clicked.connect(self.find_next.emit)
        self.prev_button.clicked.connect(self.find_previous.emit)

        layout = QVBoxLayout()
        layout.addWidget(self.find_field)
        layout.addWidget(self.next_button)
        layout.addWidget(self.prev_button)

        self.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TextEditor()
    sys.exit(app.exec_())
