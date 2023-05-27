import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        scroll_area = QScrollArea(self)  # Buat QScrollArea sebagai wadah
        self.setCentralWidget(scroll_area)

        tab_widget = QTabWidget()  # Buat objek QTabWidget
        scroll_area.setWidget(tab_widget)  # Letakkan QTabWidget di dalam QScrollArea

        # Buat widget konten untuk tab 1
        tab_content_widget = QWidget()
        tab_layout = QVBoxLayout(tab_content_widget)
        tab_layout.addWidget(QPlainTextEdit())  # Tambahkan widget yang ingin ditampilkan di dalam tab
        tab_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # Atur alignment konten
        tab_content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Atur kebijakan ukuran konten
        tab_widget.addTab(tab_content_widget, "Tab 1")  # Tambahkan tab ke QTabWidget

        # Atur scrollbar secara horizontal
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        tab_widget.setTabPosition(QTabWidget.West)  # Atur posisi tab agar scroll horizontal bekerja

# Contoh penggunaan:
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
