import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QPushButton


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setGeometry(50, 50, 200, 200)

        self.button = QPushButton("Ambil Teks", self)
        self.button.setGeometry(50, 260, 200, 30)
        self.button.clicked.connect(self.ambil_teks)

    def ambil_teks(self):
        teks = self.text_edit.toPlainText()
        baris = teks.split('\n')
        array_teks = [line for line in baris if line.strip()]
        print(array_teks)  # Ganti dengan tindakan yang diinginkan

        # Jika Anda ingin menghapus teks dari QPlainTextEdit setelah mengambilnya
        # self.text_edit.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.setGeometry(300, 300, 300, 350)
    main_window.show()
    sys.exit(app.exec_())
