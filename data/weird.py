import codecs
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class WeirdTextWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weird Text Generator")
        self.setFixedSize(500, 500)
        icon = QIcon("img/weird.png")
        self.setWindowIcon(icon)
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.input_label = QLabel("Input Text : ")
        self.input_box = QLineEdit()
        self.generate_btn = QPushButton("Generate")
        self.generate_btn.clicked.connect(self.main_weird)
        self.text_result = QTextEdit()
        self.text_result.setFixedHeight(400)
        self.text_result.setFontPointSize(12)
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.close)
        
        sub_layout = QHBoxLayout()
        sub_layout.addWidget(self.input_label)
        sub_layout.addWidget(self.input_box)
        
        layout.addLayout(sub_layout)
        layout.addWidget(self.generate_btn)
        layout.addWidget(self.text_result)
        layout.addWidget(self.ok_btn)
        
        # self.setLayout(layout)

    def main_weird(self):
        text_input = self.input_box.text()
        t = "weird_text/wt"
        path_list = []
        result = ""
        
        path_list = ["{}{}".format(t, i) for i in range(1, 27)]
        result_list = [self.convertText(path, text_input) for path in path_list]
        result = '\n\n'.join(result_list)
        self.text_result.setText(result)

    def convertText(self, path, text):
        input = text
        result = ""
        
        with codecs.open(path, "r", "utf-8") as file:
            list_text = file.read()
        
        char_len = len(list_text)
        
        if char_len == 26:
            char_list = list(list_text)
        else:
            x = char_len // 26
            char_list = [list_text[i:i+x] for i in range(0, len(list_text), x)]
            
        for char in input:
            if char.isalpha():
                index = ord(char.upper()) - ord('A')
                if index >= 0 and index < len(char_list):
                    result += char_list[index]
            else:
                result += char
                
        return result