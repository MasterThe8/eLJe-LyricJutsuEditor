import sys
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(16, 16)) # Mengatur ukuran ikon toolbar
        
        self.addToolBar(self.toolbar)
        
        self.new_action = QAction(QIcon('icons/new.png'), 'New', self)
        self.toolbar.addAction(self.new_action)
        
        self.open_action = QAction(QIcon('icons/open.png'), 'Open', self)
        self.toolbar.addAction(self.open_action)
        
        self.save_action = QAction(QIcon('icons/save.png'), 'Save', self)
        self.toolbar.addAction(self.save_action)
        
        self.toolbar.addSeparator() # Menambahkan pemisah antara aksi toolbar
        
        self.cut_action = QAction(QIcon('icons/cut.png'), 'Cut', self)
        self.toolbar.addAction(self.cut_action)
        
        self.copy_action = QAction(QIcon('icons/copy.png'), 'Copy', self)
        self.toolbar.addAction(self.copy_action)
        
        self.paste_action = QAction(QIcon('icons/paste.png'), 'Paste', self)
        self.toolbar.addAction(self.paste_action)
        
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #333;
                spacing: 3px;
            }
            
            QToolButton {
                background-color: #444;
                border: none;
                color: white;
                padding: 5px;
            }
            
            QToolButton:hover {
                background-color: #555;
            }
            
            QToolButton:pressed {
                background-color: #666;
            }
        """)  # Mengatur gaya stylesheet untuk toolbar
        
        self.setWindowTitle('Toolbar Example')
        self.setGeometry(300, 300, 300, 200)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
