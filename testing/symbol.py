import sys
import codecs
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QAbstractItemView, QMessageBox, QStyledItemDelegate
from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5.QtGui import QClipboard

# Model Tabel Kustom untuk menampilkan simbol
class SymbolTableModel(QAbstractTableModel):
    def __init__(self, symbols, parent=None):
        super().__init__(parent)
        self.symbols = symbols
        self.num_columns = 10

    def rowCount(self, parent):
        return len(self.symbols)

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
    def __init__(self, symbols):
        super().__init__()
        self.setWindowTitle("Symbol Table")
        self.setFixedSize(450, 600)

        # Buat tabel
        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setModel(SymbolTableModel(symbols))
        self.table.horizontalHeader().setVisible(False)
        
        center_delegate = CenterDelegate()
        self.table.setColumnWidth(0, 20)
        self.table.setColumnWidth(1, 20)
        self.table.setColumnWidth(2, 20)
        self.table.setColumnWidth(3, 20)
        self.table.setColumnWidth(4, 20)
        self.table.setColumnWidth(5, 20)
        self.table.setColumnWidth(6, 20)
        self.table.setColumnWidth(7, 20)
        self.table.setColumnWidth(8, 20)
        self.table.setColumnWidth(9, 20)
        self.table.setItemDelegateForColumn(0, center_delegate)
        self.table.setItemDelegateForColumn(1, center_delegate)
        self.table.setItemDelegateForColumn(2, center_delegate)
        self.table.setItemDelegateForColumn(3, center_delegate)
        self.table.setItemDelegateForColumn(4, center_delegate)
        self.table.setItemDelegateForColumn(5, center_delegate)
        self.table.setItemDelegateForColumn(6, center_delegate)
        self.table.setItemDelegateForColumn(7, center_delegate)
        self.table.setItemDelegateForColumn(8, center_delegate)
        self.table.setItemDelegateForColumn(9, center_delegate)

        # Hubungkan sinyal klik dengan slot
        self.table.clicked.connect(self.copySymbolToClipboard)

        self.setCentralWidget(self.table)

    def copySymbolToClipboard(self, index):
        symbol = self.table.model().data(index, Qt.DisplayRole)
        clipboard = QApplication.clipboard()
        clipboard.setText(symbol)

        QMessageBox.information(self, "Symbol Copied", f"Symbol '{symbol}' has been copied to clipboard.")

# Fungsi utama
def main():
    app = QApplication(sys.argv)

    # Import simbol dari file
    with codecs.open("sym.txt", "r", "utf-8") as file:
        symbols = file.read()

    window = SymbolTableWindow(symbols)
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
