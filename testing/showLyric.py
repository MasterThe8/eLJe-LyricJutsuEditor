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
        
        values = []
        current_phrase = []
        for line in lines:
            if line.strip() != "":
                event_start_index = line.find('"')
                event_end_index = line.rfind('"')
                
                event_name = line[event_start_index + 1: event_end_index].strip()
                value = line[event_end_index + 1:].strip()
                
                if event_name == "phrase_start":
                    if current_phrase:
                        values.append(" ".join(current_phrase))
                        current_phrase = []
                else:
                    current_phrase.append(value)
                    
        if current_phrase:
            values.append(" ".join(current_phrase))

        richTextEdit = self.tabWidget.widget(1)  # Mengambil objek QTextEdit pada tab "RichText Tab"
        richTextEdit.setPlainText("\n".join(current_phrase))  # Menampilkan nilai-nilai di QTextEdit

    def onRichTextChanged(self):
        richTextEdit = self.sender()  # Mendapatkan objek QTextEdit yang memicu sinyal
        values = richTextEdit.toPlainText().split("\n")  # Mendapatkan nilai-nilai dari QTextEdit

        plainTextEdit = self.tabWidget.widget(0)  # Mengambil objek QPlainTextEdit pada tab "PlainText Tab"
        plainText = plainTextEdit.toPlainText()  # Mendapatkan isi teks dari QPlainTextEdit

        lines = plainText.split("\n")  # Memisahkan setiap baris

        modified_lines = []
        for i, line in enumerate(lines):
            if line.strip() != "":
                value = values[i] if i < len(values) else ""
                modified_line = line[:line.find('"') + 1] + value + line[line.rfind('"'):]
                modified_lines.append(modified_line)

        modified_text = "\n".join(modified_lines)
        plainTextEdit.setPlainText(modified_text)  # Memperbarui nilai di QPlainTextEdit

# Contoh penggunaan:
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
