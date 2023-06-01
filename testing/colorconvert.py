from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit
from PyQt5.QtGui import QTextDocument, QTextCursor, QTextCharFormat, QColor
from PyQt5.QtCore import Qt

def convert_html_color(html_color):
    # Mengonversi kode warna HTML ke format QColor HEX
    color = QColor()
    color.setNamedColor(html_color)
    return color

def apply_custom_colors(text_edit):
    # Mendapatkan teks dari QTextEdit
    text = text_edit.toPlainText()
    
    # Mendapatkan dokumen QTextEdit
    document = text_edit.document()
    
    # Menghapus semua format teks yang ada pada dokumen
    cursor = QTextCursor(document)
    cursor.select(QTextCursor.Document)
    cursor.setCharFormat(QTextCharFormat())
    
    # Mencari semua tag HTML <color> dalam teks
    start_pos = 0
    while True:
        start_pos = text.find("<color>", start_pos)
        if start_pos == -1:
            break
        
        end_pos = text.find("</color>", start_pos)
        if end_pos == -1:
            break
        
        # Mendapatkan teks warna kustom di antara tag <color> dan </color>
        color_text = text[start_pos + len("<color>"):end_pos]
        
        # Mendapatkan format teks untuk menerapkan warna kustom
        char_format = QTextCharFormat()
        color = convert_html_color(color_text)
        char_format.setForeground(color)
        
        # Menerapkan format teks pada tag <color>
        cursor.setPosition(start_pos, QTextCursor.MoveAnchor)
        cursor.setPosition(end_pos + len("</color>"), QTextCursor.KeepAnchor)
        cursor.setCharFormat(char_format)
        
        # Menggeser posisi awal pencarian ke posisi setelah tag </color>
        start_pos = end_pos + len("</color>")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.text_edit = QTextEdit(self)
        self.setCentralWidget(self.text_edit)

        # Menjalankan fungsi apply_custom_colors setiap kali teks diubah
        self.text_edit.textChanged.connect(self.apply_custom_colors)

    def apply_custom_colors(self):
        # Memanggil fungsi untuk menerapkan warna kustom pada teks
        apply_custom_colors(self.text_edit)


if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec_()
