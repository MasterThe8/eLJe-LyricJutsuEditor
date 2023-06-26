import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class LCJutsu(QDialog):
    def __init__(self, main_window):
        super().__init__()

        self.setWindowTitle("Lyric Color no Jutsu (method 2)")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.center_window(300,500)
        self.resize(300, 250)
        self.main_window = main_window

        # Membuat layout utama
        layout = QVBoxLayout()
        
        image_label = QLabel()
        pixmap = QPixmap("img/lyricolor2.png")
        image_label.setPixmap(pixmap.scaled(280,150))
        layout.addWidget(image_label)

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

        # Membuat tombol OK dan Cancel
        self.okButton = QPushButton('OK')
        self.okButton.clicked.connect(self.mainLCJutsu)
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.reject)

        # Menambahkan tombol ke layout
        layout.addWidget(self.okButton)
        layout.addWidget(self.cancelButton)

        # Inisialisasi atribut
        self.selected_color = None
        # Tampilkan warna default
        default_color = QColor("#fca101")
        self.selected_color = default_color.name(QColor.HexRgb)
        self.color_label.setStyleSheet("background-color: {}; border: 1px solid #000; text-align: center;".format(default_color.name()))
        self.color_label.setText(default_color.name() + " (default)")
        
        # Mengatur layout utama dialog
        self.setLayout(layout)
        
    def center_window(self, width, height):
        screen = QDesktopWidget().screenGeometry()
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.setGeometry(x, y, width, height)

    def show_color_picker(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = color.name(QColor.HexRgb)
            self.color_label.setStyleSheet("background-color: {}; border: 1px solid #000; text-align: center;".format(color.name()))
            self.color_label.setText(color.name())

    def sort_script_by_position(self, script):
        sorted_script = sorted(script, key=lambda line: int(line.split(' = ')[0]))
        return sorted_script

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
            elif event_name == 'phrase_start' or event_name == 'phrase_end':
                current_position = None
                
            if current_position is not None and pos != position:
                current_line = event

        if current_position == position:
            lines.append(current_line)
        
        return lines

    def get_lyric_item(self, events):
        lines_temp = []
        for line in events[1:]:
            pos, event_data = line.split(' = ')
            event_name, *value = event_data.strip('E "').split(' ')
            value = ' '.join(value)
            if event_name != 'section':
                lines_temp.append(value)
        return lines_temp
    
    def convert_list_to_string(self, lyric_items):
        result = ''
        for i, item in enumerate(lyric_items):
            if i > 0 and not lyric_items[i-1].endswith('-'):
                result += ' '
            result += item.rstrip('-')
        return result
    
    def get_section_lines(self, script):
        section_lines = []
        for line in script:
            parts = line.split(' = ')
            if len(parts) == 2:
                pos, event_data = parts
                event_name = event_data.strip('E "').split(' ')[0]
                if event_name == 'section':
                    section_lines.append(line)
        return section_lines

    def remove_section_lines(self, script):
        filtered_script = []
        for line in script:
            parts = line.split(' = ')
            if len(parts) == 2:
                event_name = parts[1].strip('E "').split(' ')[0]
                if event_name != 'section':
                    filtered_script.append(line)
            else:
                filtered_script.append(line)
        return filtered_script

    def find_first_lyric_element(self, lyric_items):
        first_lyric_element = None
        for item in lyric_items:
            if 'lyric' in item:
                first_lyric_element = item
                lyric_items.remove(item)
                break
        return first_lyric_element

    def find_last_lyric_element(self, lyric_items):
        last_lyric_element = None
        for item in reversed(lyric_items):
            if 'lyric' in item:
                last_lyric_element = item
                lyric_items.remove(item)
                break
        return last_lyric_element

    def split_lyric(self, lyric):
        parts = lyric.split(' = E "lyric ')
        position = int(parts[0])
        lyric_value = parts[1].strip('"')
        return position, lyric_value

    def get_lyric_item(self, events):
        lines_temp = []
        for line in events[1:]:
            pos, event_data = line.split(' = ')
            event_name, *value = event_data.strip('E "').split(' ')
            value = ' '.join(value)
            if event_name != 'section':
                lines_temp.append(value)
        return lines_temp

    def convert_list_to_string(self, lyric_items):
        result = ''
        for i, item in enumerate(lyric_items):
            if i > 0 and not lyric_items[i-1].endswith('-'):
                result += ' '
            result += item.rstrip('-')
        return result

    def insert_and_sort(self, script, element):
        if isinstance(element, list):
            script.extend(element)
        elif isinstance(element, str):
            script.append(element)

        sorted_script = sorted(script, key=lambda x: int(x.split(' = ')[0]))
        return sorted_script

    def apply_lyric_color(self, lyric, pos, syllable):
        result = []
        
        if self.selected_color is None:
            hex_value = "#fca101"
        else:
            hex_value = str(self.selected_color)
        
        if '-' in syllable:
            line1 = str(int(pos) - 4) + " = E \"lyric " + lyric + "\""
            line2 = str(int(pos) - 3) + " = E \"phrase_start\""
            line3 = str(int(pos) - 2) + " = E \"lyric -\""
            line4 = str(int(pos) - 1) + " = E \"phrase_start\""
            line5 = str(int(pos)) + " = E \"lyric <color=#FFFFFF><color=" + hex_value + ">" + syllable + "\""
        else:
            line1 = str(int(pos) - 4) + " = E \"lyric " + lyric + "\""
            line2 = str(int(pos) - 3) + " = E \"phrase_start\""
            line3 = str(int(pos) - 2) + " = E \"lyric -\""
            line4 = str(int(pos) - 1) + " = E \"phrase_start\""
            line5 = str(int(pos)) + " = E \"lyric <color=#FFFFFF><color=" + hex_value + ">" + syllable + " " + "\""
            
        result.append(line1)
        result.append(line2)
        result.append(line3)
        result.append(line4)
        result.append(line5)
        return result

    def apply_lyric_close(self, pos, syllable):
        last_phrase = str(int(pos)) + " = E \"lyric " + syllable + "</color></color>\""
        return last_phrase
    
    def remove_elements(self, list1, list2):
        list1 = [x for x in list1 if x not in list2]
        return list1
    
    def check_position_in_script(self, script, position):
        for line in script:
            if line.startswith(str(position) + ' = '):
                return True
        return False

    def mainLCJutsu(self):
        positionInput = self.input_box.text()
        position = None
        if positionInput.isdigit():
            position = int(positionInput)
        else:
            QMessageBox.critical(self, "Error", "Position must be filled correctly!")
            self.show()
        
        if position is not None:
            value = self.main_window.getScript()
            value = value.splitlines()
            
            if self.check_position_in_script(value, position):
                temp_section = self.get_section_lines(value)
                temp_value = self.remove_section_lines(value)
                
                lines = self.get_lines(value, position)    
                temp_value = self.remove_elements(temp_value, lines)
                lines = self.remove_section_lines(lines)
                lyric_items = self.get_lyric_item(lines)
                lyric_items = self.convert_list_to_string(lyric_items)
                first_lyric = self.find_first_lyric_element(lines)
                last_lyric = self.find_last_lyric_element(lines)
                f_pos, f_value = self.split_lyric(first_lyric)
                l_pos, l_value = self.split_lyric(last_lyric) 
                
                first_phrase = self.apply_lyric_color(lyric_items, f_pos, f_value)
                last_phrase = self.apply_lyric_close(l_pos, l_value)
                
                lines = self.insert_and_sort(lines, first_phrase)
                lines = self.insert_and_sort(lines, last_phrase)
                
                final_result = self.insert_and_sort(temp_value, lines)
                final_result = self.insert_and_sort(final_result, temp_section)
                # final_result = self.remove_duplicates(final_result)
                final_result = '\n'.join(final_result)

                scroll_bar = self.main_window.plainTextEdit.verticalScrollBar()
                scroll_pos = scroll_bar.value()
                self.main_window.plainTextEdit.setPlainText(final_result)
                scroll_bar.setValue(scroll_pos)

                shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
                shortcut_undo.activated.connect(self.undo_text)
                shortcut_redo = QShortcut(QKeySequence("Ctrl+Y"), self)
                shortcut_redo.activated.connect(self.redo_text)
                
                super(LCJutsu, self).accept()
            else:
                QMessageBox.critical(self, "Error", "Position not found!")
                self.show()

    def reject(self):
        super(LCJutsu, self).reject()
        
    def undo_text(self):
        self.main_window.plainTextEdit.undo()
    def redo_text(self):
        self.main_window.plainTextEdit.redo() 
        

