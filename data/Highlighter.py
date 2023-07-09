import configparser
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)
        
        # [Highlight]
        # positionformat = #FF00FF
        # valueformat = #F5FF5E
        # htmltagformat = #00FF7F
        # eventnameformat = #03FCF4
        
        self.config = configparser.ConfigParser()
        self.config.read('setting.ini')
        for section in self.config.sections():
            for key, value in self.config.items(section):
                if key == 'positionformat':
                    positionColor = value
                elif key == 'valueformat':
                    valueColor = value
                elif key == 'htmltagformat':
                    htmltagColor = value
                elif key == 'eventnameformat':
                    eventnameColor = value
                
        self.highlightingRules = []

        positionFormat = QTextCharFormat()
        positionFormat.setForeground(QColor(positionColor))
        self.highlightingRules.append((QRegExp("(\\b[a-zA-Z0-9_]+)\\s*(?==)"), positionFormat))
        
        valueFormat = QTextCharFormat()
        valueFormat.setForeground(QColor(valueColor))
        self.highlightingRules.append((QRegExp('\".*\"'), valueFormat))
        self.highlightingRules.append((QRegExp('\'.*\''), valueFormat))
        
        htmlFormat = QTextCharFormat()
        htmlFormat.setForeground(QColor(htmltagColor)) 
        self.highlightingRules.append((QRegExp('<[^>]+>'), htmlFormat))
        
        # Event Highlight
        eventNameFormat = QTextCharFormat()
        eventNameFormat.setForeground(QColor(eventnameColor))
        eventName = ["Default","default", "Section", "section", "phrase_start","phrase_end","lyric","idle","half_tempo","normal_tempo","verse","chorus","music_start","lighting ()","lighting (flare)","lighting (blackout)","lighting (chase)","lighting (strobe)","lighting (color1)","lighting (color2)","lighting (sweep)","crowd_lighters_fast","crowd_lighters_off","crowd_lighters_slow","crowd_half_tempo","crowd_normal_tempo","crowd_double_tempo","band_jump","sync_head_bang","sync_wag"]

        for i in eventName:
            temp = i
            self.highlightingRules.append((QRegExp(temp), eventNameFormat))
            
    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)
