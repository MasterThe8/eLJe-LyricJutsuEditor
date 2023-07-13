import sys
import codecs
from functools import partial
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

# Model Tabel Kustom untuk menampilkan simbol
class SymbolTableModel(QAbstractTableModel):
    def __init__(self, symbols, parent=None):
        super().__init__(parent)
        self.symbols = symbols
        self.num_columns = 10

    def rowCount(self, parent):
        return 74

    def columnCount(self, parent):
        return self.num_columns

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            symbol_index = row * self.num_columns + col
            if symbol_index < len(self.symbols):
                return self.symbols[symbol_index]

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return f"Column {section + 1}"

        
class CenterDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        option.displayAlignment = Qt.AlignCenter
        super().paint(painter, option, index)

# SubWindow yang menampilkan tabel simbol
class SymbolTableWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Get Symbol")
        self.setFixedSize(432, 600)
        icon = QIcon("img/symbol.png")
        self.setWindowIcon(icon)
        
        # desc = QLabel('Daftar simbol yg work di lyric CH, gak tau kalo di YARG :p<br>Uda dites <b style="color:#FF0000;">M</b><b style="color:#FF003E;">a</b><b style="color:#FF0064;">s</b><b style="color:#FF00A2;">t</b><b style="color:#FF00D8;">e</b><b style="color:#E800FF;">r</b><b style="color:#B900FF;">T</b><b style="color:#8700FF;">h</b><b style="color:#6100FF;">e</b><b style="color:#000FFF;">8</b> dan dirapikan <b style="color:#00e9ff;">I</b><b style="color:#0beaee;">s</b><b style="color:#15ecdd;">m</b><b style="color:#20edcc;">a</b><b style="color:#2befbb;">y</b><b style="color:#36f0aa;">a</b> <b style="color:#4bf388;">M</b><b style="color:#56f577;">e</b><b style="color:#61f666;">l</b><b style="color:#6bf855;">a</b><b style="color:#76f944;">s</b><b style="color:#81fb33;">r</b><b style="color:#8cfc22;">a</b><b style="color:#96fe11;">n</b><b style="color:#a1ff00;">a</b>')
        desc = QLabel('Daftar simbol yg work di lyric CH, gak tau kalo di YARG :p<br>Uda dites <b>MasterThe8</b> dan dirapikan <b>Ismaya Melasrana</b>.<br><br>Click the symbol column and it will be automatically<br>copied to your clipboard.')
        desc.setStyleSheet("text-align: center; font-size: 14px")
        
        # Import simbol dari file
        letters = ""
        math = ""
        emoticon = ""
        symb = ""
        shape = ""
        with codecs.open("symbols/letters", "r", "utf-8") as file:
            letters = file.read()
        with codecs.open("symbols/math", "r", "utf-8") as file:
            math = file.read()
        with codecs.open("symbols/emoticon", "r", "utf-8") as file:
            emoticon = file.read()
        with codecs.open("symbols/sym", "r", "utf-8") as file:
            symb = file.read()
        with codecs.open("symbols/shape", "r", "utf-8") as file:
            shape = file.read()
        
        symbols = letters + math + emoticon + symb + shape
        # Buat tabel
        self.table = QTableView()
        model = SymbolTableModel(symbols)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setStyleSheet("QTableView::item:selected { background-color: blue; font-smoothing: antialiased;}")
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setModel(model)
        self.table.horizontalHeader().setVisible(False)
        
        center_delegate = CenterDelegate()
        col = 10
        for i in range(col):
            self.table.setColumnWidth(i, 20)
            self.table.setItemDelegateForColumn(i, center_delegate)
        
        # Periksa dan hapus kolom-kolom kosong
        empty_columns = []
        for col in range(model.columnCount(None)):
            empty = True
            for row in range(model.rowCount(None)):
                index = model.index(row, col)
                if model.data(index, Qt.DisplayRole):
                    empty = False
                    break
            if empty:
                empty_columns.append(col)

        # Hapus kolom-kolom kosong dari model tabel
        for col in reversed(empty_columns):
            model.removeColumn(col)

        # Hubungkan sinyal klik dengan slot
        self.table.clicked.connect(self.copySymbolToClipboard)
        
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        font = QFont("Arial", 12)
        font.setStyleStrategy(QFont.PreferAntialias)
        self.table.setFont(font)

        layout = QVBoxLayout()
        layout.addWidget(desc)
        layout.addWidget(self.table)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def copySymbolToClipboard(self, index):
        symbol = self.table.model().data(index, Qt.DisplayRole)
        clipboard = QApplication.clipboard()
        clipboard.setText(symbol)
        QTimer.singleShot(200, partial(self.delayedSelection, index.column()))
        self.statusBar.showMessage(f"Symbol '{symbol}' has been copied to clipboard.")
        
    def delayedSelection(self, column):
        self.table.clearSelection()
        self.table.selectColumn(column)