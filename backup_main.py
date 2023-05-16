import sys
import typing
import chardet
import codecs
import re
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QAction, QFileDialog, QDialog,  QFontDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QScrollBar, QVBoxLayout, QWidget, QScrollArea, QAbstractScrollArea, QLineEdit, QComboBox
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter, QTextCursor
from PyQt5.QtCore import Qt, QRegExp

from data import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chart File Editor")
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
        
        # Find Action
        find_action = QAction("Find", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.find_text)
        
        # Replace Action
        replace_action = QAction("Replace", self)
        replace_action.setShortcut("Ctrl+H")
        replace_action.triggered.connect(self.replace_text)
        
        # Add Jutsu Action
        addjutsu_action = QAction("Add Jutsu", self)
        addjutsu_action.triggered.connect(self.add_jutsu)
         
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
        self.toolbar = self.addToolBar("Find")
        self.toolbar.addAction(find_action)
        self.toolbar = self.addToolBar("Replace")
        self.toolbar.addAction(replace_action)
        self.toolbar = self.addToolBar("Add Jutsu")
        self.toolbar.addAction(addjutsu_action)
        
        # Add Widget
        central_widget = QLabel("Chart File Editor")
        self.setCentralWidget(central_widget)

        # Membuat objek QPlainTextEdit sebagai editor teks
        self.text_edit = QPlainTextEdit(self)
        self.setCentralWidget(self.text_edit)
        
        # Styling QPlainTextEdit
        self.highlighter = Highlighter(self.text_edit.document())
        self.text_edit.setStyleSheet("background-color: #282a36; color: #FFF;")
        font = QFont()
        font.setPointSize(12)
        font.setFamily("Consolas")
        self.text_edit.setFont(font)
        
    # Fungsi Open File
    def open_file(self):
        # Dialog Open File
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open file', '.', 'Chart files (*.chart)')
        
        # Membaca dan menampilkan textnya pada jendela
        if file_name:
            with open(file_name, 'rb') as f:
                file_contents = f.read()
                encoding = chardet.detect(file_contents)['encoding']
                # display_text = file_contents.decode().split('{')[1].split('}')[0]
                
                sync_track_text = file_contents.decode()[file_contents.decode().find('[SyncTrack]'):file_contents.decode().find('}', file_contents.decode().find('[SyncTrack]'))+1]
                
                sync_temp1 = sync_track_text.split('{')
                txtemp = 'replaced'
                sync_temp2 = sync_temp1[1].replace('}', '')
                
                synctrack_text = sync_temp1[0] + '{\n' + txtemp + '\n}'
                
                song_text = file_contents.decode()[file_contents.decode().find('[Song]'):file_contents.decode().find('}', file_contents.decode().find('[Song]'))+1]

            
            with open(file_name, 'r', encoding=encoding) as f:
                file_contents = f.read()
                display_text = file_contents[file_contents.find('{')+1:file_contents.find('}')]
                
            # self.text_edit.setPlainText(file_contents)
            
            self.text_edit.setPlainText(synctrack_text + '\n==========\n' + sync_temp2)

    # Fungsi Save File
    def save_file(self):
        # Dialog Save File
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Chart Files (*.chart)")

        # Menyimpan file berdasarkan nama file yang diambil sebelumnya
        if file_name:
            with open(file_name, 'wb') as f:
                f.write(self.text_edit.toPlainText().encode())

            with open(file_name, 'rb') as f:
                file_contents = f.read()
                encoding = chardet.detect(file_contents)['encoding']

            with open(file_name, 'w', encoding=encoding) as f:
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

    # Fungsi Find Text
    def find_text(plainTextEdit):
        dialog = FindTextDialog(plainTextEdit.window())
        plainTextEdit = main_window.text_edit
        
        if dialog.exec_() == QDialog.Accepted:
            text = dialog.text()
            cursor = plainTextEdit.document().find(text)
            if not cursor.isNull():
                plainTextEdit.setTextCursor(cursor)
                plainTextEdit.ensureCursorVisible()

    # Fungsi Replace Text
    def replace_text(plainTextEdit):
        dialog = ReplaceTextDialog(plainTextEdit.window())
        plainTextEdit = main_window.text_edit
        
        while dialog.exec_() == QDialog.Accepted:
            find_text = dialog.find_text()
            replace_text = dialog.replace_text()
            cursor = plainTextEdit.document().find(find_text)
            if cursor.isNull():
                break

            # Menggunakan for loop dengan memanfaatkan iterator dari find
            for cursor in iter(cursor, QPlainTextEdit.DocumentEnd):
                plainTextEdit.setTextCursor(cursor)
                plainTextEdit.ensureCursorVisible()

                if dialog.sender() == dialog.replace_button:
                    plainTextEdit.textCursor().insertText(replace_text)
                    break  # Hentikan loop setelah penggantian pertama
                elif dialog.sender() == dialog.replace_all_button:
                    plainTextEdit.textCursor().insertText(replace_text)

            # Pindahkan cursor ke akhir dokumen
            plainTextEdit.moveCursor(QTextCursor.End)

    
    # Fungsi Add Jutsu     
    def add_jutsu(plainTextEdit):
        dialog = AddJutsu(plainTextEdit.window())
        plainTextEdit = main_window.text_edit
        
        if dialog.exec_() == QDialog.Accepted:
            text = ""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())