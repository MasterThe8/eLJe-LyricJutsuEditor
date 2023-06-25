import sys
import typing
from PyQt5 import QtCore
import chardet
import codecs
import re
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)
        
        # Warna untuk masing-masing jenis teks
        # keywordFormat = QTextCharFormat()
        # keywordFormat.setForeground(Qt.darkBlue)
        # keywordFormat.setFontWeight(QFont.Bold)
        # keywords = ['if', 'else', 'while', 'for', 'def', 'return']
        # self.highlightingRules = [(QRegExp('\\b' + keyword + '\\b'), keywordFormat)
        #                           for keyword in keywords]

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(Qt.blue)
        keywordFormat.setFontWeight(QFont.Bold)
        
        self.highlightingRules = [(QRegExp("\\bif\\b"), keywordFormat),
                                  (QRegExp("\\belse\\b"), keywordFormat),
                                  (QRegExp("\\bswitch\\b"), keywordFormat)]

        # eventFormat = QTextCharFormat()
        # eventFormat.setForeground(QColor('#03FCF4'))
        # eventNames = ['Default','default','phrase_start','phrase_end','lyric ','idle','play','half_tempo','normal_tempo','verse','chorus','music_start','lighting ()','lighting (flare)','lighting (blackout)','lighting (chase)','lighting (strobe)','lighting (color1)','lighting (color2)','lighting (sweep)','crowd_lighters_fast','crowd_lighters_off','crowd_lighters_slow','crowd_half_tempo','crowd_normal_tempo','crowd_double_tempo','band_jump','sync_head_bang','sync_wag']
        # self.highlightingRules = [(QRegExp('\b' + eventName + '\b'), eventFormat) for eventName in eventNames]
        
        classFormat = QTextCharFormat()
        classFormat.setFontWeight(QFont.Bold)
        classFormat.setForeground(Qt.white)
        self.highlightingRules.append((QRegExp('\\b[A-Z][a-z]+\\b'), classFormat))

        variableFormat = QTextCharFormat()
        variableFormat.setForeground(QColor('#FF00FF'))
        self.highlightingRules.append((QRegExp("(\\b[a-zA-Z0-9_]+)\\s*(?==)"), variableFormat))
        
        quotationFormat = QTextCharFormat()
        quotationFormat.setForeground(QColor('#F5FF5E'))
        self.highlightingRules.append((QRegExp('\".*\"'), quotationFormat))
        self.highlightingRules.append((QRegExp('\'.*\''), quotationFormat))
        
        htmlFormat = QTextCharFormat()
        htmlFormat.setForeground(QColor('#00FF7F')) 
        self.highlightingRules.append((QRegExp('<[^>]+>'), htmlFormat))

        defaultFormat = QTextCharFormat()
        defaultFormat.setForeground(QColor('#03FCF4'))
        self.highlightingRules.append((QRegExp('Default'), defaultFormat))
        
        # Event Highlight
        # eventName = ['Default','default','phrase_start','phrase_end','lyric ','idle','play','half_tempo','normal_tempo','verse','chorus','music_start','lighting ()','lighting (flare)','lighting (blackout)','lighting (chase)','lighting (strobe)','lighting (color1)','lighting (color2)','lighting (sweep)','crowd_lighters_fast','crowd_lighters_off','crowd_lighters_slow','crowd_half_tempo','crowd_normal_tempo','crowd_double_tempo','band_jump','sync_head_bang','sync_wag']
        eventFormat = QTextCharFormat()
        eventFormat.setForeground(QColor('#03FCF4'))
        eventName = ["Default","default", "Section", "section", "phrase_start","phrase_end","lyric","idle","play","half_tempo","normal_tempo","verse","chorus","music_start","lighting ()","lighting (flare)","lighting (blackout)","lighting (chase)","lighting (strobe)","lighting (color1)","lighting (color2)","lighting (sweep)","crowd_lighters_fast","crowd_lighters_off","crowd_lighters_slow","crowd_half_tempo","crowd_normal_tempo","crowd_double_tempo","band_jump","sync_head_bang","sync_wag"]

        for i in eventName:
            temp = i
            self.highlightingRules.append((QRegExp(temp), eventFormat))
            


    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)
