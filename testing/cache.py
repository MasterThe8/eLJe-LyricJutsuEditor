import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QDialogButtonBox


class DialogWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dialog Window")

        # Membuat layout utama
        layout = QVBoxLayout()

        # Membuat label dan input box
        self.label = QLabel("Masukkan teks:")
        self.input_box = QLineEdit()

        # Membuat checkbox
        self.checkbox = QCheckBox("Centang saya")

        # Menambahkan komponen ke layout
        layout.addWidget(self.label)
        layout.addWidget(self.input_box)
        layout.addWidget(self.checkbox)

        # Membuat tombol OK dan Cancel
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Menambahkan tombol ke layout
        layout.addWidget(self.button_box)

        # Mengatur layout utama dialog
        self.setLayout(layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    dialog = DialogWindow()
    if dialog.exec_() == QDialog.Accepted:
        # Mengeksekusi kode jika tombol OK ditekan
        input_text = dialog.input_box.text()
        checked = dialog.checkbox.isChecked()
        print("Input Text:", input_text)
        print("Checkbox Checked:", checked)

    sys.exit(app.exec_())
