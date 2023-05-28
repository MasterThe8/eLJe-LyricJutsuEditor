from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QPlainTextEdit, QTextEdit, QVBoxLayout, QWidget
import sys
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.tabWidget = QTabWidget(self)
        self.tabWidget.addTab(self.tabPlainTextEdit(), 'PlainText Tab')
        self.tabWidget.addTab(self.tabRichTextEdit(), 'RichText Tab')

        self.setCentralWidget(self.tabWidget)

    def tabPlainTextEdit(self):
        plainTextEdit = QPlainTextEdit(self)
        plainTextEdit.textChanged.connect(self.onPlainTextChanged)
        return plainTextEdit

    def tabRichTextEdit(self):
        richTextEdit = QTextEdit(self)
        richTextEdit.setReadOnly(True)  # Mengatur RichTextEdit agar hanya bisa dibaca
        return richTextEdit

    def onPlainTextChanged(self):
        plainTextEdit = self.sender()  # Mendapatkan objek QPlainTextEdit yang memicu sinyal
        text = plainTextEdit.toPlainText()  # Mendapatkan isi teks dari QPlainTextEdit
        event_name = ["Default","default", "Section", "section", "phrase_start","phrase_end","lyric","idle","play","half_tempo","normal_tempo","verse","chorus","music_start","lighting ()","lighting (flare)","lighting (blackout)","lighting (chase)","lighting (strobe)","lighting (color1)","lighting (color2)","lighting (sweep)","crowd_lighters_fast","crowd_lighters_off","crowd_lighters_slow","crowd_half_tempo","crowd_normal_tempo","crowd_double_tempo","band_jump","sync_head_bang","sync_wag"]
                    
        lines = text.split("\n")
        
        position = []
        event_name_temp = []
        values = []
        
        for val in lines:
            position_temp = lines.split()
            if  len(val) > 0:
                

# Contoh penggunaan:
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
