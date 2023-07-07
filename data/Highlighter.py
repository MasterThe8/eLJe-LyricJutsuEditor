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

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(Qt.blue)
        keywordFormat.setFontWeight(QFont.Bold)
        
        self.highlightingRules = [(QRegExp("\\bif\\b"), keywordFormat),
                                  (QRegExp("\\belse\\b"), keywordFormat),
                                  (QRegExp("\\bswitch\\b"), keywordFormat)]

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
        
        # Event Highlight
        eventFormat = QTextCharFormat()
        eventFormat.setForeground(QColor('#03FCF4'))
        eventName = ["Default","default", "Section", "section", "phrase_start","phrase_end","lyric","idle","half_tempo","normal_tempo","verse","chorus","music_start","lighting ()","lighting (flare)","lighting (blackout)","lighting (chase)","lighting (strobe)","lighting (color1)","lighting (color2)","lighting (sweep)","crowd_lighters_fast","crowd_lighters_off","crowd_lighters_slow","crowd_half_tempo","crowd_normal_tempo","crowd_double_tempo","band_jump","sync_head_bang","sync_wag"]

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
