import sys
import typing
import chardet
import codecs
import re
from data import *
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
        
        
class GlobalText:
    sync_track_text = ''
    song_text = ''
    events_temp = ''
    
    single = ''
    double_guitar = ''
    double_bass = ''
    double_rhythm = ''
    keyboard = ''
    drums = ''
    
    ghl_guitar = ''
    ghl_bass = ''
    ghl_rhythm = ''
    ghl_coop = ''
    
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Menu Bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        option_menu = menu_bar.addMenu("Option")

        # File Menu & Action
        open_action = QAction('Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # Save Menu & Action
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        # Find Action
        find_action = QAction("Find", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.find_text)
        
        # Replace Action
        replace_action = QAction("Replace", self)
        replace_action.setShortcut("Ctrl+H")
        replace_action.triggered.connect(self.replace_text)
        
        # Add Jutsu Action
        addjutsu_action = QAction("Add Jutsu", self)
        addjutsu_action.triggered.connect(self.add_jutsu)
        
        # Color Picker Action
        colorpick_action = QAction("Color Picker", self)
        colorpick_action.triggered.connect(self.color_picker)
        
        # Exit Menu & Action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Font Setting
        font_setting_action = QAction("Font Setting", self)
        font_setting_action.triggered.connect(self.font_setting)
        option_menu.addAction(font_setting_action)

        # Toolbar
        self.toolbar = self.addToolBar("Open")
        self.toolbar.addAction(open_action)
        self.toolbar = self.addToolBar("Save")
        self.toolbar.addAction(save_action)
        self.toolbar = self.addToolBar("Find")
        self.toolbar.addAction(find_action)
        self.toolbar = self.addToolBar("Replace")
        self.toolbar.addAction(replace_action)
        self.toolbar = self.addToolBar("Add Jutsu")
        self.toolbar.addAction(addjutsu_action)
        self.toolbar = self.addToolBar("Color Picker")
        self.toolbar.addAction(colorpick_action)
        
        self.tabWidget = QTabWidget(self)
        self.tabWidget.addTab(self.tabPlainTextEdit(), 'PlainText Lyrics')
        self.tabWidget.addTab(self.tabRichTextEdit(), 'Display Lyrics')
        self.setCentralWidget(self.tabWidget)
        self.setWindowTitle("Chart File Editor")
        self.setGeometry(150,80, 300,300)
        self.resize(1000,600)
        self.show()
        
    def tabPlainTextEdit(self):
        self.plainTextEdit = QPlainTextEdit(self)
        self.plainTextEdit.textChanged.connect(self.onPlainTextChanged)
        self.plainTextEdit.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        # Styling QPlainTextEdit
        self.highlighter = Highlighter(self.plainTextEdit.document())
        self.plainTextEdit.setStyleSheet("background-color: #282a36; color: #FFF;")
        
        font = QFont()
        font.setPointSize(12)
        font.setFamily("Consolas, 'Courier New', monospace")
        self.plainTextEdit.setFont(font)
        
        return self.plainTextEdit
        
    def tabRichTextEdit(self):
        richTextEdit = QTextEdit(self)
        # richTextEdit.textChanged.connect(self.onRichTextChanged)
        font = QFont()
        font.setPointSize(12)
        richTextEdit.setStyleSheet("background-color: #282a36; color: #FFF;")
        font.setFamily("Consolas, 'Courier New', monospace")
        richTextEdit.setFont(font)
        
        return richTextEdit
    
    def onPlainTextChanged(self):
        plainTextEdit = self.tabWidget.currentWidget()
        richTextEdit = self.tabWidget.widget(1)
        
        plainTextEdit = self.sender()
        plainText = plainTextEdit.toPlainText()
        
        html_text = plainText.replace('\n', '<br>')
        # richText = self.convertHTMLToRichText(html_text)
        plainText_line = plainText.split('\n')
        array_teks = [line for line in plainText_line if line.strip()]
        richText = self.toRichText(array_teks)
        # print(richText)
        display = '<br>'.join(''.join(line) for line in richText)
        plainText_display = self.convertHTMLToRichText(display)
        richTextEdit.setHtml(plainText_display)
        
    def toRichText(self, plainText):
        lines = []
        current_line = ''
        for event in plainText:
            pos, event_data = event.split(' = ')
            event_name, *value = event_data.strip('E "').split(' ')
            value = ' '.join(value)
            
            if event_name == 'phrase_start':
                if current_line:
                    lines.append(current_line.strip())
                    current_line = ''
            elif event_name == 'lyric':
                if '-' in value:
                    if current_line and not current_line.endswith('-'):
                        current_line += ' '
                    current_line += value
                else:
                    current_line += ' ' + value
        
        if current_line:
            lines.append(current_line.strip())
        
        return lines
    
    def convertHTMLToRichText(self, plainText):
        rich_text = ""
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Bold)
        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)

        start_index = plainText.find("<b>")
        end_index = plainText.find("</b>")
        i_start_index = plainText.find("<i>")
        i_end_index = plainText.find("</i>")
        c_start_index = plainText.find("<color=")
        c_end_index = plainText.find("</color>")
        
        while start_index != -1 and end_index != -1 and i_start_index != -1 and i_end_index != -1 and c_start_index != -1 and c_end_index != -1:
            index = min(start_index, i_start_index, c_start_index)
            tag_end = "</b>" if start_index < i_start_index and start_index < c_start_index else "</i>" if i_start_index < c_start_index else "</color>"
            
            rich_text += plainText[:index]
            
            if tag_end == "</b>":
                text = plainText[index + 3 : end_index]
                rich_text += "<span style='font-weight: bold;'>{}</span>".format(text)
                plainText = plainText[end_index + 4:]
            elif tag_end == "</i>":
                text = plainText[index + 3 : i_end_index]
                rich_text += "<span style='font-style: italic;'>{}</span>".format(text)
                plainText = plainText[i_end_index + 4:]
            elif tag_end == "</color>":
                color_start_index = c_start_index + 8
                color_end_index = plainText.find(">", color_start_index)
                color_tag = plainText[color_start_index:color_end_index]
                color_value = color_tag.split("=")[1].strip("#>")
                text_start_index = color_end_index + 1
                text_end_index = plainText.find("</color>", text_start_index)
                text = plainText[text_start_index:text_end_index]

                rich_text += "<span style='color: {};'>{}</span>".format(color_value, text)
                
                plainText = plainText[c_end_index + 8:]

            start_index = plainText.find("<b>")
            end_index = plainText.find("</b>")
            i_start_index = plainText.find("<i>")
            i_end_index = plainText.find("</i>")
            c_start_index = plainText.find("<color=")
            c_end_index = plainText.find("</color>")

        rich_text += plainText
        return rich_text

    def color_picker(self):
        color = QColorDialog.getColor()

        if color.isValid():
            print("Selected color:", color.name())

    # ===========================================================
    
# Fungsi Open File
    def open_file(self):
        # Dialog Open File
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open file', '.', 'Chart files (*.chart)')
        
        # Membaca dan menampilkan textnya pada jendela
        if file_name:
            try:
                with open(file_name, 'rb') as f:
                    file_contents = f.read()
                    encoding = chardet.detect(file_contents)['encoding']
                    # display_text = file_contents.decode().split('{')[1].split('}')[0]
                    
                    sync_track_text = file_contents.decode()[file_contents.decode().find('[SyncTrack]'):file_contents.decode().find('}', file_contents.decode().find('[SyncTrack]'))+1]
                    
                    song_text = file_contents.decode()[file_contents.decode().find('[Song]'):file_contents.decode().find('}', file_contents.decode().find('[Song]'))+1]
                    
                    events_text = file_contents.decode()[file_contents.decode().find('[Events]'):file_contents.decode().find('}', file_contents.decode().find('[Events]'))+1]
                    events_split = events_text.split('{')
                    songrex = 'songrex'
                    
                    events_display = events_split[1].replace('}','')
                    events_temp = events_split[0] + '{\n' + songrex +'\n}\n'
                    
                    expert_single = file_contents.decode()[file_contents.decode().find('[ExpertSingle]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertSingle]'))+1]
                    hard_single = file_contents.decode()[file_contents.decode().find('[HardSingle]'):file_contents.decode().find('}', file_contents.decode().find('[HardSingle]'))+1]
                    medium_single = file_contents.decode()[file_contents.decode().find('[MediumSingle]'):file_contents.decode().find('}', file_contents.decode().find('[MediumSingle]'))+1]
                    easy_single = file_contents.decode()[file_contents.decode().find('[EasySingle]'):file_contents.decode().find('}', file_contents.decode().find('[EasySingle]'))+1]
                    
                    # DoubleGuitar
                    expert_double_guitar = file_contents.decode()[file_contents.decode().find('[ExpertDoubleGuitar]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertDoubleGuitar]'))+1]
                    hard_double_guitar = file_contents.decode()[file_contents.decode().find('[HardDoubleGuitar]'):file_contents.decode().find('}', file_contents.decode().find('[HardDoubleGuitar]'))+1]
                    medium_double_guitar = file_contents.decode()[file_contents.decode().find('[MediumDoubleGuitar]'):file_contents.decode().find('}', file_contents.decode().find('[MediumDoubleGuitar]'))+1]
                    easy_double_guitar = file_contents.decode()[file_contents.decode().find('[EasyDoubleGuitar]'):file_contents.decode().find('}', file_contents.decode().find('[EasyDoubleGuitar]'))+1]
                    
                    # DoubleBass
                    expert_double_bass = file_contents.decode()[file_contents.decode().find('[ExpertDoubleBass]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertDoubleBass]'))+1]
                    hard_double_bass = file_contents.decode()[file_contents.decode().find('[HardDoubleBass]'):file_contents.decode().find('}', file_contents.decode().find('[HardDoubleBass]'))+1]
                    medium_double_bass = file_contents.decode()[file_contents.decode().find('[MediumDoubleBass]'):file_contents.decode().find('}', file_contents.decode().find('[MediumDoubleBass]'))+1]
                    easy_double_bass = file_contents.decode()[file_contents.decode().find('[EasyDoubleBass]'):file_contents.decode().find('}', file_contents.decode().find('[EasyDoubleBass]'))+1]
                    
                    # DoubleRhythm
                    expert_double_rhythm = file_contents.decode()[file_contents.decode().find('[ExpertDoubleRhythm]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertDoubleRhythm]'))+1]
                    hard_double_rhythm = file_contents.decode()[file_contents.decode().find('[HardDoubleRhythm]'):file_contents.decode().find('}', file_contents.decode().find('[HardDoubleRhythm]'))+1]
                    medium_double_rhythm = file_contents.decode()[file_contents.decode().find('[MediumDoubleRhythm]'):file_contents.decode().find('}', file_contents.decode().find('[MediumDoubleRhythm]'))+1]
                    easy_double_rhythm = file_contents.decode()[file_contents.decode().find('[EasyDoubleRhythm]'):file_contents.decode().find('}', file_contents.decode().find('[EasyDoubleRhythm]'))+1]
                    
                    # Keyboard
                    expert_keyboard = file_contents.decode()[file_contents.decode().find('[ExpertKeyboard]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertKeyboard]'))+1]
                    hard_keyboard = file_contents.decode()[file_contents.decode().find('[HardKeyboard]'):file_contents.decode().find('}', file_contents.decode().find('[HardKeyboard]'))+1]
                    medium_keyboard = file_contents.decode()[file_contents.decode().find('[MediumKeyboard]'):file_contents.decode().find('}', file_contents.decode().find('[MediumKeyboard]'))+1]
                    easy_keyboard = file_contents.decode()[file_contents.decode().find('[EasyKeyboard]'):file_contents.decode().find('}', file_contents.decode().find('[EasyKeyboard]'))+1]
                    
                    # Drums
                    expert_drums = file_contents.decode()[file_contents.decode().find('[ExpertDrums]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertDrums]'))+1]
                    hard_drums = file_contents.decode()[file_contents.decode().find('[HardDrums]'):file_contents.decode().find('}', file_contents.decode().find('[HardDrums]'))+1]
                    medium_drums = file_contents.decode()[file_contents.decode().find('[MediumDrums]'):file_contents.decode().find('}', file_contents.decode().find('[MediumDrums]'))+1]
                    easy_drums = file_contents.decode()[file_contents.decode().find('[EasyDrums]'):file_contents.decode().find('}', file_contents.decode().find('[EasyDrums]'))+1]
                    
                    # GHLGuitar
                    expert_ghl_guitar = file_contents.decode()[file_contents.decode().find('[ExpertGHLGuitar]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertGHLGuitar]'))+1]
                    hard_ghl_guitar = file_contents.decode()[file_contents.decode().find('[HardGHLGuitar]'):file_contents.decode().find('}', file_contents.decode().find('[HardGHLGuitar]'))+1]
                    medium_ghl_guitar = file_contents.decode()[file_contents.decode().find('[MediumGHLGuitar]'):file_contents.decode().find('}', file_contents.decode().find('[MediumGHLGuitar]'))+1]
                    easy_ghl_guitar = file_contents.decode()[file_contents.decode().find('[EasyGHLGuitar]'):file_contents.decode().find('}', file_contents.decode().find('[EasyGHLGuitar]'))+1]
                    
                    # GHLBass
                    expert_ghl_bass = file_contents.decode()[file_contents.decode().find('[ExpertGHLBass]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertGHLBass]'))+1]
                    hard_ghl_bass = file_contents.decode()[file_contents.decode().find('[HardGHLBass]'):file_contents.decode().find('}', file_contents.decode().find('[HardGHLBass]'))+1]
                    medium_ghl_bass = file_contents.decode()[file_contents.decode().find('[MediumGHLBass]'):file_contents.decode().find('}', file_contents.decode().find('[MediumGHLBass]'))+1]
                    easy_ghl_bass = file_contents.decode()[file_contents.decode().find('[EasyGHLBass]'):file_contents.decode().find('}', file_contents.decode().find('[EasyGHLBass]'))+1]
                    
                    # GHLRhythm
                    expert_ghl_rhythm = file_contents.decode()[file_contents.decode().find('[ExpertGHLRhythm]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertGHLRhythm]'))+1]
                    hard_ghl_rhythm = file_contents.decode()[file_contents.decode().find('[HardGHLRhythm]'):file_contents.decode().find('}', file_contents.decode().find('[HardGHLRhythm]'))+1]
                    medium_ghl_rhythm = file_contents.decode()[file_contents.decode().find('[MediumGHLRhythm]'):file_contents.decode().find('}', file_contents.decode().find('[MediumGHLRhythm]'))+1]
                    easy_ghl_rhythm = file_contents.decode()[file_contents.decode().find('[EasyGHLRhythm]'):file_contents.decode().find('}', file_contents.decode().find('[EasyGHLRhythm]'))+1]
                    
                    # GHLCoop
                    expert_ghl_coop = file_contents.decode()[file_contents.decode().find('[ExpertGHLCoop]'):file_contents.decode().find('}', file_contents.decode().find('[ExpertGHLCoop]'))+1]
                    hard_ghl_coop = file_contents.decode()[file_contents.decode().find('[HardGHLCoop]'):file_contents.decode().find('}', file_contents.decode().find('[HardGHLCoop]'))+1]
                    medium_ghl_coop = file_contents.decode()[file_contents.decode().find('[MediumGHLCoop]'):file_contents.decode().find('}', file_contents.decode().find('[MediumGHLCoop]'))+1]
                    easy_ghl_coop = file_contents.decode()[file_contents.decode().find('[EasyGHLCoop]'):file_contents.decode().find('}', file_contents.decode().find('[EasyGHLCoop]'))+1]

                
                with open(file_name, 'r', encoding=encoding) as f:
                    file_contents = f.read()
                    display_text = file_contents[file_contents.find('{')+1:file_contents.find('}')]
                    
                # self.text_edit.setPlainText(file_contents)
                GlobalText.sync_track_text = sync_track_text + '\n'
                GlobalText.song_text = song_text + '\n'
                GlobalText.events_temp = events_temp + '\n'
                
                GlobalText.single = expert_single + '\n' + hard_single + '\n' + medium_single + '\n' + easy_single + '\n'
                GlobalText.double_guitar = expert_double_guitar + '\n' + hard_double_guitar + '\n' + medium_double_guitar + '\n' + easy_double_guitar + '\n'
                GlobalText.double_bass = expert_double_bass + '\n' + hard_double_bass + '\n' + medium_double_bass + '\n' + easy_double_bass + '\n'
                GlobalText.double_rhythm = expert_double_rhythm + '\n' + hard_double_rhythm + '\n' + medium_double_rhythm + '\n' + easy_double_rhythm + '\n'
                GlobalText.keyboard = expert_keyboard + '\n' + hard_keyboard + '\n' + medium_keyboard + '\n' + easy_keyboard + '\n'
                GlobalText.drums = expert_drums + '\n' + hard_drums + '\n' + medium_drums + '\n' + easy_drums + '\n'
                
                GlobalText.ghl_guitar = expert_ghl_guitar + '\n' + hard_ghl_guitar + '\n' + medium_ghl_guitar + '\n' + easy_ghl_guitar + '\n'
                GlobalText.ghl_bass = expert_ghl_bass + '\n' + hard_ghl_bass + '\n' + medium_ghl_bass + '\n' + easy_ghl_bass + '\n'
                GlobalText.ghl_rhythm = expert_ghl_rhythm + '\n' + hard_ghl_rhythm + '\n' + medium_ghl_rhythm + '\n' + easy_ghl_rhythm + '\n'
                GlobalText.ghl_coop = expert_ghl_coop + '\n' + hard_ghl_coop + '\n' + medium_ghl_coop + '\n' + easy_ghl_coop + '\n'
                
                display = events_display.replace('\n  ', '\n')
                self.plainTextEdit.setPlainText(display.strip())
            
            except Exception as e:
                error_message = f"Error occurred while opening file:\n{str(e)}"
                QMessageBox.critical(self, "Error", error_message)
                
    # Fungsi Save File
    def save_file(self):
        # Dialog Save File
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Chart Files (*.chart)")

        if file_name:
            with open(file_name, 'wb') as f:
                
                temp1 = GlobalText.sync_track_text + GlobalText.song_text + GlobalText.events_temp
                temp2 = GlobalText.single + GlobalText.double_guitar + GlobalText.double_bass + GlobalText.double_rhythm + GlobalText.keyboard + GlobalText.drums + GlobalText.ghl_guitar + GlobalText.ghl_bass + GlobalText.ghl_rhythm + GlobalText.ghl_coop
                
                pte = self.plainTextEdit.toPlainText()
                nl = pte.replace('\n', '\n  ')
                fl = '  ' + nl
                temp = temp1.replace("songrex", fl)
                
                temp3 = temp+temp2
                
                f.write(temp3.encode())
                
                
    def font_setting(self):
        font2, ok = QFontDialog.getFont()
        
        if ok:
            self.text_edit.setFont(font2)

    def closeEvent(self, event):
        # Membuat dialog konfirmasi untuk keluar
        confirm_dialog = QMessageBox()
        confirm_dialog.setIcon(QMessageBox.Question)
        confirm_dialog.setText("Apakah Anda yakin ingin keluar?")
        confirm_dialog.setWindowTitle("Konfirmasi Keluar")
        confirm_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm_dialog.button(QMessageBox.Yes).setText("Ya")
        confirm_dialog.button(QMessageBox.No).setText("Tidak")
        confirm_dialog.setDefaultButton(QMessageBox.No)

        # Menampilkan dialog konfirmasi
        if confirm_dialog.exec_() == QMessageBox.Yes:
            # Jika pengguna menekan tombol "Ya", keluar dari aplikasi
            event.accept()
        else:
            # Jika pengguna menekan tombol "Tidak", batalkan event close
            event.ignore()

    # Fungsi Find Text
    def find_text(plainTextEdit):
        dialog = FindTextDialog(plainTextEdit.window())
        plainTextEdit = main_window.tabWidget.currentWidget()
        
        if dialog.exec_() == QDialog.Accepted:
            text = dialog.text()
            cursor = plainTextEdit.document().find(text)
            if not cursor.isNull():
                plainTextEdit.setTextCursor(cursor)
                plainTextEdit.ensureCursorVisible()

    # Fungsi Replace Text
    def replace_text(plainTextEdit):
        dialog = ReplaceTextDialog(plainTextEdit.window())
        plainTextEdit = main_window.text_edit
        
        while dialog.exec_() == QDialog.Accepted:
            find_text = dialog.find_text()
            replace_text = dialog.replace_text()
            cursor = plainTextEdit.document().find(find_text)
            if cursor.isNull():
                break

            # Menggunakan for loop dengan memanfaatkan iterator dari find
            for cursor in iter(cursor, QPlainTextEdit.DocumentEnd):
                plainTextEdit.setTextCursor(cursor)
                plainTextEdit.ensureCursorVisible()

                if dialog.sender() == dialog.replace_button:
                    plainTextEdit.textCursor().insertText(replace_text)
                    break  # Hentikan loop setelah penggantian pertama
                elif dialog.sender() == dialog.replace_all_button:
                    plainTextEdit.textCursor().insertText(replace_text)

            # Pindahkan cursor ke akhir dokumen
            plainTextEdit.moveCursor(QTextCursor.End)

    
    # Fungsi Add Jutsu
    def add_jutsu(plainTextEdit):
        dialog = AddJutsu(plainTextEdit.window())
        plainTextEdit = main_window.text_edit
        
        if dialog.exec_() == QDialog.Accepted:
            text = ""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
