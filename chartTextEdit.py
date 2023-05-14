import sys
import typing
from PyQt5 import QtCore
import chardet
import codecs
from PyQt5.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QAction, QFileDialog, QDialog,  QFontDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QScrollBar, QVBoxLayout, QWidget, QScrollArea, QAbstractScrollArea, QLineEdit, QComboBox
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter, QTextCursor
from PyQt5.QtCore import Qt, QRegExp

class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)
        
        # Warna untuk masing-masing jenis teks
        # keywordFormat = QTextCharFormat()
        # keywordFormat.setForeground(Qt.darkBlue)
        # keywordFormat.setFontWeight(QFont.Bold)
        # keywords = ['if', 'else', 'while', 'for', 'def', 'return']
        # self.highlightingRules = [(QRegExp('\\b' + keyword + '\\b'), keywordFormat)
        #                           for keyword in keywords]

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(Qt.blue)
        keywordFormat.setFontWeight(QFont.Bold)
        
        self.highlightingRules = [(QRegExp("\\bif\\b"), keywordFormat),
                                  (QRegExp("\\belse\\b"), keywordFormat),
                                  (QRegExp("\\bswitch\\b"), keywordFormat)]

        # eventFormat = QTextCharFormat()
        # eventFormat.setForeground(QColor('#03FCF4'))
        # eventNames = ['Default','default','phrase_start','phrase_end','lyric ','idle','play','half_tempo','normal_tempo','verse','chorus','music_start','lighting ()','lighting (flare)','lighting (blackout)','lighting (chase)','lighting (strobe)','lighting (color1)','lighting (color2)','lighting (sweep)','crowd_lighters_fast','crowd_lighters_off','crowd_lighters_slow','crowd_half_tempo','crowd_normal_tempo','crowd_double_tempo','band_jump','sync_head_bang','sync_wag']
        # self.highlightingRules = [(QRegExp('\b' + eventName + '\b'), eventFormat) for eventName in eventNames]
        
        classFormat = QTextCharFormat()
        classFormat.setFontWeight(QFont.Bold)
        classFormat.setForeground(Qt.darkMagenta)
        self.highlightingRules.append((QRegExp('\\b[A-Z][a-z]+\\b'), classFormat))

        variableFormat = QTextCharFormat()
        variableFormat.setForeground(QColor('#FF00FF'))
        self.highlightingRules.append((QRegExp("(\\b[a-zA-Z0-9_]+)\\s*(?==)"), variableFormat))
        
        quotationFormat = QTextCharFormat()
        quotationFormat.setForeground(QColor('#F5FF5E'))
        self.highlightingRules.append((QRegExp('\".*\"'), quotationFormat))
        self.highlightingRules.append((QRegExp('\'.*\''), quotationFormat))
        
        htmlFormat = QTextCharFormat()
        htmlFormat.setForeground(QColor('#00FF7F'))
        self.highlightingRules.append((QRegExp('<[^>]+>'), htmlFormat))

        defaultFormat = QTextCharFormat()
        defaultFormat.setForeground(QColor('#03FCF4'))
        self.highlightingRules.append((QRegExp('Default'), defaultFormat))
        
        # Event Highlight
        # eventName = ['Default','default','phrase_start','phrase_end','lyric ','idle','play','half_tempo','normal_tempo','verse','chorus','music_start','lighting ()','lighting (flare)','lighting (blackout)','lighting (chase)','lighting (strobe)','lighting (color1)','lighting (color2)','lighting (sweep)','crowd_lighters_fast','crowd_lighters_off','crowd_lighters_slow','crowd_half_tempo','crowd_normal_tempo','crowd_double_tempo','band_jump','sync_head_bang','sync_wag']
        eventFormat = QTextCharFormat()
        eventFormat.setForeground(QColor('#03FCF4'))
        eventName = ["Default","default", "Section", "section", "phrase_start","phrase_end","lyric","idle","play","half_tempo","normal_tempo","verse","chorus","music_start","lighting ()","lighting (flare)","lighting (blackout)","lighting (chase)","lighting (strobe)","lighting (color1)","lighting (color2)","lighting (sweep)","crowd_lighters_fast","crowd_lighters_off","crowd_lighters_slow","crowd_half_tempo","crowd_normal_tempo","crowd_double_tempo","band_jump","sync_head_bang","sync_wag"]

        for i in eventName:
            temp = i
            self.highlightingRules.append((QRegExp(temp), eventFormat))
            
    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

class FindTextDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Find Text")
        
        self.label = QLabel("Find what:")
        self.line_edit = QLineEdit()
        
        self.find_button = QPushButton("Find")
        self.find_button.setDefault(True)
        self.find_button.setEnabled(False)
        
        self.cancel_button = QPushButton("Cancel")
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.find_button)
        layout.addWidget(self.cancel_button)
        
        self.setLayout(layout)
        
        self.line_edit.textChanged.connect(self.enable_find_button)
        self.find_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
    def enable_find_button(self, text):
        self.find_button.setEnabled(bool(text))
        
    def text(self):
        return self.line_edit.text()

class ReplaceTextDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Replace Text")
        
        self.find_label = QLabel("Find what:")
        self.find_line_edit = QLineEdit()
        
        self.replace_label = QLabel("Replace with:")
        self.replace_line_edit = QLineEdit()
        
        self.find_button = QPushButton("Find")
        self.find_button.setDefault(True)
        self.find_button.setEnabled(False)
        
        self.replace_button = QPushButton("Replace")
        self.replace_button.setEnabled(False)
        
        self.replace_all_button = QPushButton("Replace All")
        self.replace_all_button.setEnabled(False)
        
        self.cancel_button = QPushButton("Cancel")
        
        layout = QVBoxLayout()
        layout.addWidget(self.find_label)
        layout.addWidget(self.find_line_edit)
        layout.addWidget(self.replace_label)
        layout.addWidget(self.replace_line_edit)
        layout.addWidget(self.find_button)
        layout.addWidget(self.replace_button)
        layout.addWidget(self.replace_all_button)
        layout.addWidget(self.cancel_button)
        
        self.setLayout(layout)
        
        self.find_line_edit.textChanged.connect(self.enable_find_button)
        self.replace_line_edit.textChanged.connect(self.enable_replace_buttons)
        self.find_button.clicked.connect(self.accept)
        self.replace_button.clicked.connect(self.accept)
        self.replace_all_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
    def enable_find_button(self, text):
        self.find_button.setEnabled(bool(text))
        
    def enable_replace_buttons(self, text):
        self.replace_button.setEnabled(bool(text))
        self.replace_all_button.setEnabled(bool(text))
        
    def find_text(self):
        return self.find_line_edit.text()
    
    def replace_text(self):
        return self.replace_line_edit.text()

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
            # with open(file_name, 'r') as f:
            #     file_contents = f.read()
            with open(file_name, 'rb') as f:
                file_contents = f.read()
                encoding = chardet.detect(file_contents)['encoding']

            with open(file_name, 'r', encoding=encoding) as f:
                file_contents = f.read()
            self.text_edit.setPlainText(file_contents)

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
        
        while True:
            if dialog.exec_() == QDialog.Accepted:
                find_text = dialog.find_text()
                replace_text = dialog.replace_text()
                cursor = plainTextEdit.document().find(find_text)
                if not cursor.isNull():
                    plainTextEdit.setTextCursor(cursor)
                    plainTextEdit.ensureCursorVisible()
                    
                    if dialog.sender() == dialog.replace_button:
                        plainTextEdit.textCursor().insertText(replace_text)
                    elif dialog.sender() == dialog.replace_all_button:
                        while not cursor.isNull():
                            plainTextEdit.textCursor().insertText(replace_text)
                            cursor = plainTextEdit.document().find(find_text, cursor)
                else:
                    break
            else:
                break
    
    # Fungsi Add Jutsu     
    def add_jutsu(plainTextEdit):
        dialog = AddJutsu(plainTextEdit.window())
        plainTextEdit = main_window.text_edit
        
        if dialog.exec_() == QDialog.Accepted:
            text = ""

class AddJutsu(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Add Lyric Jutsu")
        self.setGeometry(420, 240, 300, 300)
        self.resize(400, 200)
        
        layout = QVBoxLayout()
        self.comboBox = QComboBox()
        self.comboBox.addItems(['No SlideUp Transition', 'Hide Next Phrase'])
        self.lineEdit = QLineEdit()
        self.positionEdit = QLineEdit()
        
        self.positionLabel = QLabel('Input Position :')
        self.jutsuLabel = QLabel('Pilih Jutsu')
        self.textLabel = QLabel('Input Lyric :')
        
        self.okButton = QPushButton('OK')
        self.okButton.clicked.connect(self.accept)
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.reject)
        
        layout.addWidget(self.positionLabel)
        layout.addWidget(self.positionEdit)
        layout.addWidget(self.jutsuLabel)
        layout.addWidget(self.comboBox)
        layout.addWidget(self.textLabel)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.okButton)
        layout.addWidget(self.cancelButton)
        self.setLayout(layout)
    
    # def insertTextAtCursor(plaintext, text):
    # cursor = plaintext.textCursor()
    # cursor.insertText(text)
    # plaintext.setTextCursor(cursor)
    
    def accept(self):
        # index = self.comboBox.currentIndex()
        # jutsuSelected = self.comboBox.itemText(index)
        jutsuSelected = self.comboBox.currentText()
        positionInput = self.positionEdit.text()
        position = int(positionInput)
        lyricInput = self.lineEdit.text()
        
        jutsuInput = ""
        
        if jutsuSelected == 'No SlideUp Transition':
            line1 = "  " + str(position) + " = E \"lyric _\""
            line2 = "  " + str(position+1) + " = E \"phrase_start\""
            line3 = "  " + str(position+2) + " = E \"lyric "+lyricInput+"\""
            jutsuInput = line1 + '\n' + line2 + '\n' + line3
            
        elif jutsuSelected == 'Hide Next Phrase':
            line1 = "  " + str(position) + " = E \"lyric _\""
            line2 = "  " + str(position+1) + " = E \"phrase_start\""
            line3 = "  " + str(position+2) + " = E \"lyric _\""
            line4 = "  " + str(position+3) + " = E \"phrase_start\""
            line5 = "  " + str(position+4) + " = E \"lyric "+lyricInput+"\""
            jutsuInput = line1 + '\n' + line2 + '\n' + line3 + '\n' + line4 + '\n' + line5
        
        cursor = self.parent().text_edit.textCursor()
        cursor.insertText(str(jutsuInput))
        self.parent().text_edit.setTextCursor(cursor)
        
        super(AddJutsu, self).accept()
    
    def reject(self):
        super(AddJutsu, self).reject()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
