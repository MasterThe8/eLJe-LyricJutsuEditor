import configparser
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class SettingHighlight(QDialog):
    def __init__(self, main_window):
        super().__init__()
        
        self.main_window = main_window
        
        self.setWindowTitle("Highligter Setting")
        self.setFixedSize(180, 250)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        main_layout = QVBoxLayout()
        
        layout1 = QHBoxLayout()
        self.colorpick_btn1 = QPushButton("Position")
        self.colorlabel_1 = QLabel()
        self.colorpick_btn1.clicked.connect(self.show_color_picker_1)
        self.colorlabel_1.setFixedHeight(21)
        layout1.addWidget(self.colorpick_btn1)
        layout1.addWidget(self.colorlabel_1)
        
        layout2 = QHBoxLayout()
        self.colorpick_btn2 = QPushButton("Value")
        self.colorlabel_2 = QLabel()
        self.colorpick_btn2.clicked.connect(self.show_color_picker_2)
        self.colorlabel_2.setFixedHeight(21)
        layout2.addWidget(self.colorpick_btn2)
        layout2.addWidget(self.colorlabel_2)

        layout3 = QHBoxLayout()
        self.colorpick_btn3 = QPushButton("Tag")
        self.colorlabel_3 = QLabel()
        self.colorpick_btn3.clicked.connect(self.show_color_picker_3)
        self.colorlabel_3.setFixedHeight(21)
        layout3.addWidget(self.colorpick_btn3)
        layout3.addWidget(self.colorlabel_3)

        layout4 = QHBoxLayout()
        self.colorpick_btn4 = QPushButton("Event Name")
        self.colorlabel_4 = QLabel()
        self.colorpick_btn4.clicked.connect(self.show_color_picker_4)
        self.colorlabel_4.setFixedHeight(21)
        layout4.addWidget(self.colorpick_btn4)
        layout4.addWidget(self.colorlabel_4)

        main_layout.addLayout(layout1)
        main_layout.addLayout(layout2)
        main_layout.addLayout(layout3)
        main_layout.addLayout(layout4)
        
        self.config = configparser.ConfigParser()
        self.config.read('setting.ini')
        for section in self.config.sections():
            for key, value in self.config.items(section):
                if key == 'positionformat':
                    color1 = value
                elif key == 'valueformat':
                    color2 = value
                elif key == 'htmltagformat':
                    color3 = value
                elif key == 'eventnameformat':
                    color4 = value
                    
        position_color = QColor(color1)
        value_color = QColor(color2)
        htmltag_color = QColor(color3)
        event_name_color = QColor(color4)
        
        self.setColor1 = position_color.name()
        self.setColor2 = value_color.name()
        self.setColor3 = htmltag_color.name()
        self.setColor4 = event_name_color.name()
        
        self.colorlabel_1.setStyleSheet("background-color: {}; padding: 1px; border: 1px solid #000; text-align: center;".format(position_color.name()))
        self.colorlabel_1.setText(self.setColor1)
        self.colorlabel_2.setStyleSheet("background-color: {}; padding: 1px;border: 1px solid #000; text-align: center;".format(value_color.name()))
        self.colorlabel_2.setText(self.setColor2)
        self.colorlabel_3.setStyleSheet("background-color: {}; padding: 1px;border: 1px solid #000; text-align: center;".format(htmltag_color.name()))
        self.colorlabel_3.setText(self.setColor3)
        self.colorlabel_4.setStyleSheet("background-color: {}; padding: 1px;border: 1px solid #000; text-align: center;".format(event_name_color.name()))
        self.colorlabel_4.setText(self.setColor4)
        
        button_layout = QHBoxLayout()
        setdefault_btn = QPushButton('Set Default')
        apply_btn = QPushButton('Apply')
        close_btn = QPushButton('Close')
        
        setdefault_btn.clicked.connect(self.set_default_highlight)
        apply_btn.clicked.connect(self.apply_color_higlight)
        close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(close_btn)
        
        main_layout.addWidget(setdefault_btn)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)

    def show_color_picker_1(self):
        color = QColorDialog.getColor()
        if color.isValid():
            selected_color = color.name(QColor.HexRgb)
            self.colorlabel_1.setStyleSheet("background-color: {}; border: 1px solid #000; text-align: center;".format(color.name()))
            self.colorlabel_1.setText(color.name())
            self.setColor1 = selected_color
            
    def show_color_picker_2(self):
        color = QColorDialog.getColor()
        if color.isValid():
            selected_color = color.name(QColor.HexRgb)
            self.colorlabel_2.setStyleSheet("background-color: {}; border: 1px solid #000; text-align: center;".format(color.name()))
            self.colorlabel_2.setText(color.name())
            self.setColor2 = selected_color

    def show_color_picker_3(self):
        color = QColorDialog.getColor()
        if color.isValid():
            selected_color = color.name(QColor.HexRgb)
            self.colorlabel_3.setStyleSheet("background-color: {}; border: 1px solid #000; text-align: center;".format(color.name()))
            self.colorlabel_3.setText(color.name())
            self.setColor3 = selected_color

    def show_color_picker_4(self):
        color = QColorDialog.getColor()
        if color.isValid():
            selected_color = color.name(QColor.HexRgb)
            self.colorlabel_4.setStyleSheet("background-color: {}; border: 1px solid #000; text-align: center;".format(color.name()))
            self.colorlabel_4.setText(color.name())
            self.setColor4 = selected_color
            
    def set_default_highlight(self):
        # [Highlight]
        defColor1 = '#FF00FF'
        defColor2 = '#F5FF5E'
        defColor3 = '#00FF7F'
        defColor4 = '#03FCF4'

        self.colorlabel_1.setStyleSheet("background-color: {}; border: 1px solid #000; text-align: center;".format(defColor1))
        self.colorlabel_1.setText(defColor1)
        self.colorlabel_2.setStyleSheet("background-color: {}; border: 1px solid #000; text-align: center;".format(defColor2))
        self.colorlabel_2.setText(defColor2)
        self.colorlabel_3.setStyleSheet("background-color: {}; border: 1px solid #000; text-align: center;".format(defColor3))
        self.colorlabel_3.setText(defColor3)
        self.colorlabel_4.setStyleSheet("background-color: {}; border: 1px solid #000; text-align: center;".format(defColor4))
        self.colorlabel_4.setText(defColor4)
        
        config = configparser.ConfigParser()
        config.read('setting.ini')
        for section in config.sections():
            for key, value in config.items(section):
                if key == 'positionformat':
                    config.set(section, key, defColor1)
                    with open('setting.ini', 'w') as configfile:
                        config.write(configfile)
                elif key == 'valueformat':
                    config.set(section, key, defColor2)
                    with open('setting.ini', 'w') as configfile:
                        config.write(configfile)
                elif key == 'htmltagformat':
                    config.set(section, key, defColor3)
                    with open('setting.ini', 'w') as configfile:
                        config.write(configfile)
                elif key == 'eventnameformat':
                    config.set(section, key, defColor4)
                    with open('setting.ini', 'w') as configfile:
                        config.write(configfile)
    
        self.main_window.update_highlighter()
            
    def apply_color_higlight(self):
        config = configparser.ConfigParser()
        config.read('setting.ini')
        for section in config.sections():
            for key, value in config.items(section):
                if key == 'positionformat':
                    config.set(section, key, str(self.setColor1))
                    with open('setting.ini', 'w') as configfile:
                        config.write(configfile)
                elif key == 'valueformat':
                    config.set(section, key, str(self.setColor2))
                    with open('setting.ini', 'w') as configfile:
                        config.write(configfile)
                elif key == 'htmltagformat':
                    config.set(section, key, str(self.setColor3))
                    with open('setting.ini', 'w') as configfile:
                        config.write(configfile)
                elif key == 'eventnameformat':
                    config.set(section, key, str(self.setColor4))
                    with open('setting.ini', 'w') as configfile:
                        config.write(configfile)
    
        self.main_window.update_highlighter()
    