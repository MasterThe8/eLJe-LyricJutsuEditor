import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QRadioButton, QVBoxLayout, QWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Radio Button Example")
        
        self.radio_button1 = QRadioButton("Option 1")
        self.radio_button2 = QRadioButton("Option 2")
        self.radio_button3 = QRadioButton("Option 3")
        
        layout = QVBoxLayout()
        layout.addWidget(self.radio_button1)
        layout.addWidget(self.radio_button2)
        layout.addWidget(self.radio_button3)
        
        widget = QWidget()
        widget.setLayout(layout)
        
        self.setCentralWidget(widget)
        
        self.radio_button1.setChecked(True)
        
        self.radio_button1.clicked.connect(self.handle_radio_button)
        self.radio_button2.clicked.connect(self.handle_radio_button)
        self.radio_button3.clicked.connect(self.handle_radio_button)
    
    def handle_radio_button(self):
        radio_button = self.sender()
        
        if radio_button.isChecked():
            print(f"Radio button {radio_button.text()} is checked")

app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec_())
