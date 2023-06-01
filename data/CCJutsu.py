import sys
from PyQt5.QtWidgets import QApplication, QDialog, QColorDialog, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QDialogButtonBox, QPushButton, QHBoxLayout
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QColor

class CCJutsu(QDialog):
    def __init__(self, main_window):
        super().__init__()

        self.setWindowTitle("Dialog Window")
        
        self.main_window = main_window

        # Membuat layout utama
        layout = QVBoxLayout()

        # Membuat label dan input box
        self.label = QLabel("Input Lyric Position:")
        self.input_box = QLineEdit()

        # Membuat layout untuk input hex dan color picker
        input_hex_layout = QHBoxLayout()
        self.input_hex = QLineEdit()
        self.color_picker_button = QPushButton("Pick Color")
        self.color_picker_button.clicked.connect(self.show_color_picker)
        self.color_label = QLabel()

        # Menambahkan komponen ke layout
        layout.addWidget(self.label)
        layout.addWidget(self.input_box)

        # Menambahkan input hex dan color picker ke layout
        # input_hex_layout.addWidget(self.input_hex)
        input_hex_layout.addWidget(self.color_picker_button)
        input_hex_layout.addWidget(self.color_label)

        layout.addLayout(input_hex_layout)

        # Membuat checkbox
        self.checkbox = QCheckBox("Hide Next Phrase")
        layout.addWidget(self.checkbox)

        # Membuat tombol OK dan Cancel
        self.okButton = QPushButton('OK')
        self.okButton.clicked.connect(self.ccjutsu)
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.reject)

        # Menambahkan tombol ke layout
        layout.addWidget(self.okButton)
        layout.addWidget(self.cancelButton)

        # Inisialisasi atribut
        self.selected_color = None

        # Mengatur layout utama dialog
        self.setLayout(layout)

    def show_color_picker(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = color.name(QColor.HexRgb)
            self.color_label.setStyleSheet("background-color: {}".format(color.name()))
            self.color_label.setText(color.name())
        
    def get_lines(self, events, position):
        lines = []
        current_line = ''
        current_position = None

        for event in events:
            pos, event_data = event.split(' = ')
            event_name, *value = event_data.strip('E "').split(' ')
            value = ' '.join(value)
            
            pos = int(pos)

            if current_position == position:
                lines.append(current_line)
            
            if pos == position:
                current_position = pos
                current_line = event
            elif event_name == 'phrase_start':
                current_position = None

            if current_position is not None and pos != position:
                current_line = event

        if current_position == position:
            lines.append(current_line)
        
        return lines

    def cc(self, lines):
        result = []
        previous_lyric = ''
        temp = lines[:]
        hex_value = str(self.selected_color)
        
        for line in lines:
            pos, event_data = line.split(' = ')
            event_name, *value = event_data.strip('E "').split(' ')
            value = ' '.join(value)
            lyric = ''.join([str(element) for element in value if element != '-'])
            
            if '-' in value:
                line1 = str(int(pos)) + " = E \"lyric <i></i>\""
                line2 = str(int(pos) + 1) + " = E \"phrase_start\""
                line3 = str(int(pos) + 2) + " = E \"lyric <color=" + hex_value + ">" + previous_lyric + lyric + "</color>\""
                line = line1 + '\n' + line2 + '\n' + line3
                previous_lyric += lyric
            else:
                line1 = str(int(pos)) + " = E \"lyric <i></i>\""
                line2 = str(int(pos) + 1) + " = E \"phrase_start\""
                line3 = str(int(pos) + 2) + " = E \"lyric <color=" + hex_value + ">" + previous_lyric + lyric + ' ' + "</color>\""
                line = line1 + '\n' + line2 + '\n' + line3
                previous_lyric += lyric + ' '
            
            result.append(line)
            # previous_lyric += lyric
        return result

    def get_lyric_item(self, events):
        lines_temp = []
        for line in events[1:]:
            pos, event_data = line.split(' = ')
            event_name, *value = event_data.strip('E "').split(' ')
            value = ' '.join(value)
            lines_temp.append(value)
        return lines_temp

    def add_next_lyric(self, lines, script):
        script_temp = {int(item.split(' = ')[0]): item.split(' = ')[1] for item in script}

        temp_lyric = lines.copy()
        value_to_insert = []
        color_values = []
        
        # Remove '- ' in lyric
        for i in range(len(temp_lyric)):
            temp = ' '.join(temp_lyric[i:])
            result = ''.join(temp).replace('- ', '')
            if '</color>_' in temp_lyric:
                lyric_result = '<color=#FFFFFF> '+result+'</color>'
            else:
                lyric_result = '<color=#FFFFFF>'+result+'</color>'
            value_to_insert.append(lyric_result)

        # Get line with </color>
        for key, value in script_temp.items():
            if "</color>" in value:
                color_values.append(value)

        length_value_to_insert = len(value_to_insert)
        length_color_values = len(color_values)

        # Replace </color> with </color>+lyric
        for i in range(length_color_values - 1):
            if i < length_value_to_insert:
                color_values[i] = color_values[i].replace('</color>', f'</color>{value_to_insert[i]}')
                
        # Mengembalikan nilai color_values ke dalam script
        for i, key in enumerate(script_temp):
            if "</color>" in script_temp[key]:
                script_temp[key] = color_values.pop(0)

        # for i,j in script_temp.items():
        #     print(f'{i} = {j}')
            
        script_result = [f"{key} = {value}" for key, value in script_temp.items()]

        return script_result

    def ccjutsu(self):
        positionInput = self.input_box.text()
        position = int(positionInput)
        value = self.main_window.getScript()

        value = value.splitlines()
        lines = self.get_lines(value, position)
        result = self.cc(lines)
        # temp_lines = lines.copy()
        result_split = [line for i in result for line in i.split('\n')]
        lyric_items = self.get_lyric_item(lines)
        last_result = self.add_next_lyric(lyric_items, result_split)
        
        
        index = next((i for i, event in enumerate(value) if event.startswith(str(position) + ' = ')), None)

        if index is not None:
            del value[index]
            value[index:index] = last_result
        
        # Pengecekan dan penghapusan baris dengan nomor yang sama
        existing_numbers = set()
        i = 0
        while i < len(value):
            event_parts = value[i].split(' = ')
            if len(event_parts) >= 2:
                event_number = event_parts[0]
                if event_number in existing_numbers:
                    del value[i]
                    continue
                else:
                    existing_numbers.add(event_number)
            i += 1
        
        
        lines_text = '\n'.join(value)
        self.main_window.plainTextEdit.setPlainText(lines_text)
        
        super(CCJutsu, self).accept()
        
    def reject(self):
        super(CCJutsu, self).reject()
            
        
    