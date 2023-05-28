import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QAction, QDialog, QLabel, QLineEdit, QTextEdit, QVBoxLayout, QDialogButtonBox


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Main Window")
        self.setGeometry(100, 100, 500, 400)

        self.text_edit = QPlainTextEdit(self)
        self.setCentralWidget(self.text_edit)

        self.dialog_action = QAction("Buka Dialog", self)
        self.dialog_action.triggered.connect(self.open_dialog)
        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("File")
        self.file_menu.addAction(self.dialog_action)

    def open_dialog(self):
        dialog = Dialog(self.text_edit.toPlainText())
        dialog.exec_()


class Dialog(QDialog):
    def __init__(self, text):
        super().__init__()

        self.setWindowTitle("Dialog")
        self.layout = QVBoxLayout()

        self.input_label = QLabel("Masukkan nilai:")
        self.input_text = QLineEdit()
        self.input_text.returnPressed.connect(self.get_value)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.get_value)
        self.button_box.rejected.connect(self.reject)

        self.layout.addWidget(self.input_label)
        self.layout.addWidget(self.input_text)
        self.layout.addWidget(self.output_text)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)

        self.text = text

    def get_value(self):
        
        value = self.input_text.text()
        
        lines = self.text.split("\n")
        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
