import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QFontDialog, QPlainTextEdit, QAction, QDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
from PyQt5.QtGui import QFont

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Python File Editor")
        self.setGeometry(150,80, 300,300)
        self.resize(1000,600)
        
        # Menu Bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        option_menu = menu_bar.addMenu("Option")
        
        # File Menu & Action
        open_action = QAction('Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # Save Menu & Action
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        # Exit Menu & Action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Font Setting
        font_setting_action = QAction("Font Setting", self)
        font_setting_action.triggered.connect(self.font_setting)
        option_menu.addAction(font_setting_action)

        # Toolbar
        self.toolbar = self.addToolBar("Open")
        self.toolbar.addAction(open_action)
        self.toolbar = self.addToolBar("Save")
        self.toolbar.addAction(save_action)
        
        # Add Widget
        central_widget = QLabel("Python File Editor")
        self.setCentralWidget(central_widget)

        # Membuat objek QPlainTextEdit sebagai editor teks
        self.text_edit = QPlainTextEdit(self)
        self.setCentralWidget(self.text_edit)
        
        # Styling QPlainTextEdit
        self.text_edit.setStyleSheet("background-color: #111; color: #FFF;")
        font = QFont()
        font.setPointSize(10)
        font.setFamily("Consolas")
        self.text_edit.setFont(font)

    # Fungsi Open File
    def open_file(self):
        # Dialog Open File
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open file', '.', 'Python files (*.py)')
        
        # Membaca dan menampilkan textnya pada jendela
        if file_name:
            with open(file_name, 'r') as f:
                file_contents = f.read()
            self.text_edit.setPlainText(file_contents)

    # Fungsi Save File
    def save_file(self):
        # Dialog Save File
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Python Files (*.py)")

        # Menyimpan file berdasarkan nama file yang diambil sebelumnya
        if file_name:
            with open(file_name, "wt") as f:
                f.write(self.text_edit.toPlainText())

    def font_setting(self):
        font2, ok = QFontDialog.getFont()
        
        if ok:
            self.text_edit.setFont(font2)
            
    def closeEvent(self, event):
        # Membuat dialog konfirmasi untuk keluar
        confirm_dialog = QMessageBox()
        confirm_dialog.setIcon(QMessageBox.Question)
        confirm_dialog.setText("Apakah Anda yakin ingin keluar?")
        confirm_dialog.setWindowTitle("Konfirmasi Keluar")
        confirm_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm_dialog.button(QMessageBox.Yes).setText("Ya")
        confirm_dialog.button(QMessageBox.No).setText("Tidak")
        confirm_dialog.setDefaultButton(QMessageBox.No)

        # Menampilkan dialog konfirmasi
        if confirm_dialog.exec_() == QMessageBox.Yes:
            # Jika pengguna menekan tombol "Ya", keluar dari aplikasi
            event.accept()
        else:
            # Jika pengguna menekan tombol "Tidak", batalkan event close
            event.ignore()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
