import re
import os
import sys
import codecs
import typing
import chardet
import configparser
from data import *
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class GlobalText:
    song = ''
    sync_track = ''
    events = ''
    
    note_inst = ''
    
class LandingPageWindow(QMainWindow):
    def __init__(self, main_window):
        super().__init__()
        
        self.main_window = main_window
        self.setWindowTitle("Landing Page")
        self.center_window(800,400)
        
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        central_widget.setLayout(layout)
        
        logo_label = QLabel()
        pixmap = QPixmap("img/icon.ico")
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedHeight(200)
        layout.addWidget(logo_label)
        
        label1 = QLabel()
        label1.setText("<b>eLJe | LyricJutsu Editor v0.1.0 (BETA)</b>")
        label1.setObjectName("label1")
        label1.setAlignment(Qt.AlignCenter)
        label1.setFont(QFont("Arial", 26))
        layout.addWidget(label1)

        label2 = QLabel()
        label2.setText('<b style="color:#FF0000;">M</b>'
               '<b style="color:#FF003E;">a</b>'
               '<b style="color:#FF0064;">s</b>'
               '<b style="color:#FF00A2;">t</b>'
               '<b style="color:#FF00D8;">e</b>'
               '<b style="color:#E800FF;">r</b>'
               '<b style="color:#B900FF;">T</b>'
               '<b style="color:#8700FF;">h</b>'
               '<b style="color:#6100FF;">e</b>'
               '<b style="color:#000FFF;">8</b>')
        label2.setObjectName("label2")
        label2.setFont(QFont("Arial", 18))
        layout.addWidget(label2)

        layout.addSpacing(10)

        button = QPushButton("Link Start!")
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(self.open_main_window)
        layout.addWidget(button)
        with open('style/landing.css', 'r') as f:
            style_sheet = f.read()
        self.setStyleSheet(style_sheet)

    def center_window(self, width, height):
        screen = QDesktopWidget().screenGeometry()
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.setGeometry(x, y, width, height)

    def open_main_window(self):
        self.close()
        # main_window.open_file()
        main_window.setEnabled(True)

class FileSystemModel(QFileSystemModel):
    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return ""
        return super().headerData(section, orientation, role)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            if index.column() in [1, 2, 3]:
                return self.filePath(index)
        return super().data(index, role)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.last_opened_directory = ''
        
        self.tabWidget = QTabWidget(self)
        self.tabWidget.addTab(self.tabPlainTextEdit(), 'PlainText Lyrics')
        self.tabWidget.addTab(self.tabRichTextEdit(), 'Display Lyrics')
        
        self.config = configparser.ConfigParser()
        self.config.read('setting.ini')
        for section in self.config.sections():
            for key, value in self.config.items(section):
                if key == 'path':
                    path = value
                elif key == 'font':
                    dock_font = value
                    
        self.path = path
        self.setWindowTitle("eLJe | LyricJutsu Editor v0.1.0 (BETA)")
        self.center_window(1000,600)
        # self.showMaximized()
        self.setEnabled(False)
        
        icon = QIcon("img/icon.ico")
        self.setWindowIcon(icon)
        
        # Menu Bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        option_menu = menu_bar.addMenu("Option")
        view_menu = menu_bar.addMenu("View")
        about = menu_bar.addMenu("About")
        about_show = QAction("About", self)
        about_show.triggered.connect(self.show_about)
        about.addAction(about_show)

        # File Menu & Action
        open_action = QAction(QIcon("img/open_file.png"),'Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # Save Menu & Action
        save_action = QAction(QIcon("img/save_file.png"),"Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        select_chart_path = QAction("Select Song Chart Folder", self)
        select_chart_path.triggered.connect(self.choose_directory)
        file_menu.addAction(select_chart_path)
        
        # Find Action
        find_action = QAction(QIcon("img/find.png"),"Find", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.find_text)

        # Replace Action
        replace_action = QAction(QIcon("img/replace.png"),"Replace", self)
        replace_action.setShortcut("Ctrl+H")
        replace_action.triggered.connect(self.replace_text)
        
        # Color Picker Action
        colorpick_action = QAction(QIcon("img/color_picker.png"),"Color Picker", self)
        colorpick_action.triggered.connect(self.color_picker)

        # Zoom In & Zoom Out
        self.zoom_in_action = QAction(QIcon("img/zoom_in.png"), "Zoom In", self)
        self.zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        self.zoom_in_action.triggered.connect(self.zoom_in)
        self.zoom_out_action = QAction(QIcon("img/zoom_out.png"), "Zoom Out", self)
        self.zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        self.zoom_out_action.triggered.connect(self.zoom_out)
        self.zoom_in_action.setShortcut("Ctrl+=")
        self.zoom_in_shortcut = QShortcut(QKeySequence("Ctrl+Shift++"), self)
        self.zoom_in_shortcut.activated.connect(self.zoom_in)
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+Shift+-"), self)
        self.zoom_out_shortcut.activated.connect(self.zoom_out)
        view_menu.addAction(self.zoom_in_action)
        view_menu.addAction(self.zoom_out_action)
        
        # Get Symbol
        getsymbol = QAction(QIcon("img/symbol.png"), "Get Symbol", self)
        getsymbol.triggered.connect(self.get_symbol)
        
        # Weird Text Generator
        weirdtext = QAction(QIcon("img/weird.png"), "Weird Text Generator", self)
        weirdtext.triggered.connect(self.weird_text_generator)
        
        # Add Jutsu Action
        addjutsu_action = QAction(QIcon("img/addjutsu.png"), "Add Jutsu", self)
        addjutsu_action.setShortcut("Alt+1")
        addjutsu_action.triggered.connect(self.add_jutsu)
        
        # Color no Jutsu Action
        colorjutsu_action = QAction(QIcon("img/lyricolor.png"), "Custom Color no Jutsu", self)
        colorjutsu_action.setShortcut("Alt+2")
        colorjutsu_action.triggered.connect(self.custom_color_no_jutsu)
        
        lyricolorjutsu_action = QAction(QIcon("img/lyricolor2.png"), "LyriColor no Jutsu", self)
        lyricolorjutsu_action.setShortcut("Alt+3")
        lyricolorjutsu_action.triggered.connect(self.lyric_color_no_jutsu)
        
        # ConvertPhrase no Jutsu Action
        convertjutsu_action = QAction(QIcon("img/kan2rom.png"), "Kan2Rom no Jutsu", self)
        convertjutsu_action.setShortcut("Alt+4")
        convertjutsu_action.triggered.connect(self.convert_phrase_no_jutsu)
        
        # Exit Menu & Action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Font Setting
        font_setting_action = QAction("Font Setting", self)
        font_setting_action.triggered.connect(self.font_setting)
        option_menu.addAction(font_setting_action)
        
        # Highlight Setting
        highlight_setting_action = QAction("Highlight Setting", self)
        highlight_setting_action.triggered.connect(self.highlight_setting)
        option_menu.addAction(highlight_setting_action)
        
        # Toolbar
        self.toolbar = QToolBar()
        self.toolbar.setOrientation(Qt.Horizontal)
        self.toolbar.setFixedHeight(40)
        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.addToolBar(self.toolbar)
        self.toolbar.setMovable(False)
        with open('style/toolbar.css','r') as f:
            toolbarstyle = f.read()
        self.toolbar.setStyleSheet(toolbarstyle)
        
        self.toolbar.addAction(open_action)
        self.toolbar.addAction(save_action)
        self.toolbar.addAction(find_action)
        self.toolbar.addAction(replace_action)
        self.toolbar.addAction(self.zoom_in_action)
        self.toolbar.addAction(self.zoom_out_action)
        self.toolbar.addAction(colorpick_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(getsymbol)
        self.toolbar.addAction(weirdtext)
        self.toolbar.addAction(addjutsu_action)
        self.toolbar.addAction(colorjutsu_action)
        self.toolbar.addAction(lyricolorjutsu_action)
        self.toolbar.addAction(convertjutsu_action)
        self.toolbar.addSeparator()
        
        self.toggleDisplay = QAction("Display Lyrics")
        self.toggleDisplay.setCheckable(True)
        self.toggleDisplay.setChecked(False)
        self.toggleDisplay.triggered.connect(self.toggle_display)
        self.toggleDisplay_button = QToolButton()
        self.toggleDisplay_button.setDefaultAction(self.toggleDisplay)
        self.toggleDisplay_button.setIcon(QIcon("img/display.png"))
        self.toolbar.insertWidget(None, self.toggleDisplay_button)
        self.toggleDisplay.toggled.connect(self.toggle_display_icon)
        
        self.toggleTree = QAction("Toogle TreeView", self)
        self.toggleTree.setCheckable(True)
        self.toggleTree.setChecked(True)
        self.toggleTree.triggered.connect(self.toggle_treeview)
        self.tool_button = QToolButton()
        self.tool_button.setDefaultAction(self.toggleTree)
        self.tool_button.setIcon(QIcon("img/toggle_tree_on.png"))
        self.toolbar.insertWidget(None, self.tool_button)
        self.toggleTree.toggled.connect(self.toggle_treeview_icon)
        
        # Membuat QAction untuk membuka/tutup QDockWidget
        self.toggleDockAction = QAction("Toogle DockText", self)
        self.toggleDockAction.setCheckable(True)
        self.toggleDockAction.setChecked(True)
        self.toggleDockAction.triggered.connect(self.toggleDockWidget)
        self.tool_button2 = QToolButton()
        self.tool_button2.setDefaultAction(self.toggleDockAction)
        self.tool_button2.setIcon(QIcon("img/toggle_dock_on.png"))
        self.toolbar.insertWidget(None, self.tool_button2)
        self.toggleDockAction.toggled.connect(self.toggle_dock_icon)

        # Membuat QDockWidget untuk QTreeView
        self.treeDock = QDockWidget("Song Chart Directory", self)
        self.treeDock.setFeatures(QDockWidget.AllDockWidgetFeatures)

        # Membuat tombol sebagai header widget
        button = QPushButton("Song Chart Directory")
        button.clicked.connect(self.choose_directory)
        header_layout = QHBoxLayout()
        header_layout.addWidget(button)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        self.treeDock.setTitleBarWidget(header_widget)

        # Membuat QTreeView sebagai widget
        self.treeView = QTreeView()
        self.treeDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.treeDock.setWidget(self.treeView)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.treeDock)
        
        # Mengatur path direktori dari file .txt
        self.treemodel = FileSystemModel()
        self.treemodel.setRootPath(path)
        with open('style/treeview.css','r') as f:
            treestyle = f.read()
        self.treeView.setStyleSheet(treestyle)
        self.treeView.setModel(self.treemodel)
        self.treeView.setRootIndex(self.treemodel.index(path))
        self.treeView.clicked.connect(self.handle_item_clicked)
        
        # Menyembunyikan kolom-kolom kecuali kolom "name"
        self.treeView.setHeaderHidden(True)
        headertree = self.treeView.header()
        headertree.setSectionResizeMode(0, QHeaderView.Stretch)
        for column in range(1, self.treemodel.columnCount()):
            headertree.setSectionHidden(column, True)
        
        # Memfilter tampilan file dengan format tertentu
        filter_formats = ['chart']
        name_filters = ['*.' + format for format in filter_formats]
        self.treemodel.setNameFilters(name_filters)
        self.treemodel.setNameFilterDisables(False)
        
        # Membuat QDockWidget
        self.dock = QDockWidget("Temp Text", self)
        self.dock.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.dock.setStyleSheet("background-color: #282a36; color: #FFF; font-size: 14px;")
        
        # Membuat QTextEdit sebagai widget editor teks
        self.textEdit = QTextEdit()
        textOption = self.textEdit.document().defaultTextOption()
        textOption.setWrapMode(QTextOption.NoWrap)
        self.textEdit.document().setDefaultTextOption(textOption)
        with open('style/textedit.css','r') as f:
            text_edit_style = f.read()
        self.textEdit.setStyleSheet(text_edit_style)
        self.textEdit.setFontFamily(dock_font)
        self.dock.setWidget(self.textEdit)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        
        self.setCentralWidget(self.tabWidget)
        self.show()

    def toggle_treeview(self):
        if self.toggleTree.isChecked():
            self.treeDock.show()
            self.write_treeview_status(True)
        else:
            self.treeDock.hide()
            self.write_treeview_status(False)
            
    def toggle_display(self):
        if self.toggleDisplay.isChecked():
            self.toggleDisplay.setChecked(True)
            self.write_display_status(True)
        else:
            self.toggleDisplay.setChecked(False)
            self.write_display_status(False)

    def write_display_status(self, status):
        config = configparser.ConfigParser()
        config.read('setting.ini')
        for section in config.sections():
            for key, value in config.items(section):
                if key == 'display':
                    config.set(section, key, str(status))
                    with open('setting.ini', 'w') as configfile:
                        config.write(configfile)
                        
    def write_treeview_status(self, status):
        config = configparser.ConfigParser()
        config.read('setting.ini')
        for section in config.sections():
            for key, value in config.items(section):
                if key == 'treeview':
                    config.set(section, key, str(status))
                    with open('setting.ini', 'w') as configfile:
                        config.write(configfile)
                        
    def toggle_display_icon(self, check):
        icon_checked = QIcon("img/display.png")
        icon_unchecked = QIcon("img/display.png")
        if check:
            self.toggleDisplay_button.setIcon(icon_checked)
        else:
            self.toggleDisplay_button.setIcon(icon_unchecked)
            
    def toggle_treeview_icon(self, check):
        icon_checked = QIcon("img/toggle_tree_on.png")
        icon_unchecked = QIcon("img/toggle_tree_off.png")
        if check:
            self.tool_button.setIcon(icon_checked)
        else:
            self.tool_button.setIcon(icon_unchecked)
            
    def toggleDockWidget(self):
        if self.toggleDockAction.isChecked():
            self.dock.show()
        else:
            self.dock.hide()
            
    def toggle_dock_icon(self, check):
        icon_checked = QIcon("img/toggle_dock_on.png")
        icon_unchecked = QIcon("img/toggle_dock_off.png")
        if check:
            self.tool_button2.setIcon(icon_checked)
        else:
            self.tool_button2.setIcon(icon_unchecked)
            
    def handle_item_clicked(self, index):
        file_info = self.treemodel.fileInfo(index)
        if file_info.isFile():
            file_path = file_info.filePath()
            self.read_chart(file_path)
            
        elif file_info.isDir():
            folder_path = file_info.filePath()
            
    def choose_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.config.set("Setting", "path", directory)
            with open("setting.ini", "w") as file:
                self.config.write(file)
            self.treeView.model().setRootPath(directory)
            self.treeView.setRootIndex(self.treeView.model().index(directory))

    def center_window(self, width, height):
        screen = QDesktopWidget().screenGeometry()
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.setGeometry(x, y, width, height)

    def zoom_in(self):
        font = self.plainTextEdit.font()
        font_d =  self.richTextEdit.font()
        font_size = font.pointSize()
        font_d_size = font_d.pointSize()
        font.setPointSize(font_size + 1)
        font_d.setPointSize(font_d_size + 1)
        self.plainTextEdit.setFont(font)
        self.richTextEdit.setFont(font_d)

    def zoom_out(self):
        font = self.plainTextEdit.font()
        font_d =  self.richTextEdit.font()
        font_size = font.pointSize()
        font_d_size = font_d.pointSize()
        font.setPointSize(font_size - 1)
        font_d.setPointSize(font_d_size - 1)
        self.plainTextEdit.setFont(font)
        self.richTextEdit.setFont(font_d)
        
    def undo_text(self):
        self.plainTextEdit.undo()  
    def redo_text(self):
        self.plainTextEdit.redo() 
        
    def update_highlighter(self):
        self.highlighter = Highlighter(self.plainTextEdit.document())
          
    def tabPlainTextEdit(self):
        self.plainTextEdit = QPlainTextEdit(self)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.plainTextEdit.textChanged.connect(self.onPlainTextChanged)
        self.plainTextEdit.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        self.plainTextEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.plainTextEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scrollbarv = self.plainTextEdit.verticalScrollBar()
        scrollbarh = self.plainTextEdit.horizontalScrollBar()
        
        shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
        shortcut_undo.activated.connect(self.undo_text)
        shortcut_redo = QShortcut(QKeySequence("Ctrl+Y"), self)
        shortcut_redo.activated.connect(self.redo_text)
                
        # Styling QPlainTextEdit
        with open('style/textedit.css','r') as f:
            text_edit_style = f.read()
        self.plainTextEdit.setStyleSheet(text_edit_style)
        self.highlighter = Highlighter(self.plainTextEdit.document())

        font = QFont()
        font.setPointSize(12)
        font_config = configparser.ConfigParser()
        font_config.read('setting.ini')
        for section in font_config.sections():
            for key, value in font_config.items(section):
                if key == 'font':
                    font_family = value
        font.setFamily(font_family)
        font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        self.plainTextEdit.setFont(font)
        
        return self.plainTextEdit
        
    def tabRichTextEdit(self):
        self.richTextEdit = QTextEdit(self)
        # richTextEdit.textChanged.connect(self.onRichTextChanged)
        self.richTextEdit.setReadOnly(True)
        self.richTextEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.richTextEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scrollbarv = self.richTextEdit.verticalScrollBar()
        scrollbarh = self.richTextEdit.horizontalScrollBar()

        css_file = QFile("style/textedit.css")
        if css_file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(css_file)
            stylesheet = stream.readAll()
            css_file.close()
            
            scrollbarv.setStyleSheet(stylesheet)
            scrollbarh.setStyleSheet(stylesheet)
            
        font = QFont()
        font.setPointSize(12)
        self.richTextEdit.setStyleSheet("background-color: #282a36; color: #FFF;")
        font_config = configparser.ConfigParser()
        font_config.read('setting.ini')
        for section in font_config.sections():
            for key, value in font_config.items(section):
                if key == 'font':
                    font_family = value
        font.setFamily(font_family)
        font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        self.richTextEdit.setFont(font)
        
        return self.richTextEdit
    
    def onPlainTextChanged(self):
        plainTextEdit = self.tabWidget.currentWidget()
        richTextEdit = self.tabWidget.widget(1)
        
        plainTextEdit = self.sender()
        plainText = plainTextEdit.toPlainText()
        
        config = configparser.ConfigParser()
        config.read('setting.ini')
        for section in config.sections():
            for key, value in config.items(section):
                if key == 'display':
                    display = value
        if display == 'True':
            try:
                plainText_line = plainText.split('\n')
                array_teks = [line for line in plainText_line if line.strip()]
                richText = self.toRichText(array_teks)
                display = '<br>'.join(''.join(line) for line in richText)
                plainText_display = self.convertHTMLToRichText(display)
                plainText_display = self.convert_and_set_text(plainText_display)
                richTextEdit.setHtml(plainText_display)

            except Exception:
                QMessageBox.critical(self, "Wrong event format detected!", f"You can't commit or create newline events manually.\nBut you can copy&paste events directly or edit them in Moonscraper!!")
                self.show()
        else:
            pass
                    
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
                    if current_line and not current_line.endswith('-'):
                        current_line += ' '
                    current_line += '' + value
        
        if current_line:
            lines.append(current_line.strip())
        
        return lines

    def convert_and_set_text(self, plain_text):
        color_start_tag = "<color="
        color_end_tag = "</color>"

        converted_text = plain_text
        start_index = converted_text.find(color_start_tag)

        while start_index != -1:
            end_index = converted_text.find(">", start_index)
            hex_start_index = start_index + len(color_start_tag)
            hex_end_index = converted_text.find(">", hex_start_index)
            text_start_index = end_index + 1
            text_end_index = converted_text.find(color_end_tag, text_start_index)

            if end_index != -1 and hex_end_index != -1 and text_end_index != -1:
                hex_value = converted_text[hex_start_index:hex_end_index]
                text = converted_text[text_start_index:text_end_index]

                span = "<span style='color: {};'>{}</span>".format(hex_value, text)
                converted_text = converted_text[:start_index] + span + converted_text[text_end_index + len(color_end_tag):]
            else:
                break

            start_index = converted_text.find(color_start_tag)

        # self.text_edit.setHtml(converted_text)
        return converted_text

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
        
        while start_index != -1 and end_index != -1 and i_start_index != -1 and i_end_index != -1:
            index = min(start_index, i_start_index)
            
            rich_text += plainText[:index]
            
            if index == start_index:
                text = plainText[index + 3 : end_index]
                rich_text += "<span style='font-weight: bold;'>{}</span>".format(text)
                plainText = plainText[end_index + 4:]
            else:
                text = plainText[index + 3 : i_end_index]
                rich_text += "<span style='font-style: italic;'>{}</span>".format(text)
                plainText = plainText[i_end_index + 4:]

            start_index = plainText.find("<b>")
            end_index = plainText.find("</b>")
            i_start_index = plainText.find("<i>")
            i_end_index = plainText.find("</i>")

        rich_text += plainText
        return rich_text

    def color_picker(self):
        color_dialog = QColorDialog()
        color_icon = QIcon("img/color_picker.png")
        color_dialog.setWindowIcon(color_icon)
        color = color_dialog.getColor()
        if color.isValid():
            print("Selected color:", color.name())

    # ===========================================================
    
    # Fungsi Open File
    def open_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Open File")
        file_dialog.setDirectory(self.path)
        file_name, _ = file_dialog.getOpenFileName(self, 'Open File', '.', 'Chart Files (*.chart)')

        if file_name:
            try:
                self.read_chart(file_name)
            except Exception as e:
                error_message = f"Error occurred while opening file:\n{str(e)}"
                QMessageBox.critical(self, "Error", error_message)

    def read_chart(self, file_chart):
        with open(file_chart, 'rb') as f:
            file_contents = f.read()
            encoding = chardet.detect(file_contents)['encoding']
            
            sync_track_text = file_contents.decode()[file_contents.decode().find('[SyncTrack]'):file_contents.decode().find('}', file_contents.decode().find('[SyncTrack]'))+1]
            song_text = file_contents.decode()[file_contents.decode().find('[Song]'):file_contents.decode().find('}', file_contents.decode().find('[Song]'))+1]
            
            events_text = file_contents.decode()[file_contents.decode().find('[Events]'):file_contents.decode().find('}', file_contents.decode().find('[Events]'))+1]
            events_split = events_text.split('{')
            songrex = 'songrex'
            events_display = events_split[1].replace('}','')
            events_temp = events_split[0] + '{\n' + songrex +'\n}\n'
            
            GlobalText.song = song_text + '\n'
            GlobalText.sync_track = sync_track_text + '\n'
            GlobalText.events = events_temp + '\n'
            GlobalText.note_inst = ''
            
            difficulty = ['Expert', 'Hard', 'Medium', 'Easy']
            instrumental = ['Single', 'DoubleGuitar', 'DoubleBass', 'DoubleRhythm', 'Keyboard', 'Drums', 'GHLGuitar', 'GHLBass', 'GHLRhythm', 'GHLCoop']

            fcd = file_contents.decode()

            for inst in instrumental:
                for diff in difficulty:
                    section_name = diff + inst
                    if section_name in fcd:
                        start_index = fcd.find('[' + section_name + ']')
                        end_index = fcd.find('}', fcd.find('[' + section_name + ']')) + 1
                        section_content = fcd[start_index:end_index]
                        GlobalText.note_inst += section_content + '\n'
                    else:
                        section_content = ''
                        GlobalText.note_inst += section_content
        
        display = events_display.replace('\n  ', '\n')
        self.plainTextEdit.setPlainText(display.strip())

    # Fungsi Save File
    def save_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Save File")
        file_dialog.setDirectory(self.path)
        file_name, _ = file_dialog.getSaveFileName(self, "Save File", "", "Chart Files (*.chart)")
        
        if file_name:
            with open(file_name, 'wb') as f:
                
                temp1 = GlobalText.song + GlobalText.sync_track + GlobalText.events
                temp2 = GlobalText.note_inst
                
                pte = self.plainTextEdit.toPlainText()
                nl = pte.replace('\n', '\n  ')
                fl = '  ' + nl
                temp = temp1.replace("songrex", fl)
                
                temp3 = temp+temp2
                
                f.write(temp3.encode())

    def closeEvent(self, event):
        confirm_dialog = QMessageBox()
        confirm_dialog.setIcon(QMessageBox.Question)
        confirm_dialog.setText("Are you sure want to exit?")
        confirm_dialog.setWindowTitle("Exit")
        confirm_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm_dialog.button(QMessageBox.Yes).setText("Yes")
        confirm_dialog.button(QMessageBox.No).setText("No")
        confirm_dialog.setDefaultButton(QMessageBox.No)

        if confirm_dialog.exec_() == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
            
    def font_setting(self):
        font2, ok = QFontDialog.getFont()

        if ok:
            font_name = font2.toString()
            self.config.set("Setting", "font", font_name)
            with open("setting.ini", "w") as file:
                self.config.write(file)
            self.plainTextEdit.setFont(font2)
            self.richTextEdit.setFont(font2)
            
    def highlight_setting(self):
        high_dial = SettingHighlight(self)
        high_dial.exec_()

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
                
    def replace_text(self):
        dialog = Replace(self)
        dialog.exec_()
        
    def get_symbol(self):
        self.symbol_window = SymbolTableWindow()
        self.symbol_window.show()
        
    def weird_text_generator(self):
        self.weird_window = WeirdTextWindow()
        self.weird_window.show()
        
    def add_jutsu(plainTextEdit):
        dialog = AddJutsu(plainTextEdit.window())
        plainTextEdit = main_window.tabWidget.currentWidget()
        dialog.setWindowFlags(dialog.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        dialog.exec_()
            
    def custom_color_no_jutsu(self):
        dialog = CCJutsu(self)
        dialog.exec_()
        
    def convert_phrase_no_jutsu(self):
        dialog = CnvrtJutsu(self)
        dialog.exec_()
        
    def lyric_color_no_jutsu(self):
        dialog = LCJutsu(self)
        dialog.exec_()
    
    def getScript(self):
        plainTextEdit = self.tabWidget.currentWidget()
        plainText = plainTextEdit.toPlainText()

        return plainText
    
    def show_about(self):
        about_window = AboutWindow()
        about_window.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    # main_window.show()
    landing_page = LandingPageWindow(main_window)
    landing_page.show()
    sys.exit(app.exec_())
