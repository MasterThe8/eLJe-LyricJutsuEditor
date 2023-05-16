import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QPlainTextEdit, QTextEdit
from PyQt5.QtGui import QTextDocument
from PyQt5.QtCore import Qt

class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.tabWidget = QTabWidget(self)
        self.tabWidget.addTab(self.createPlainTextTab(), 'Tab 1')
        self.tabWidget.addTab(self.createRichTextTab(), 'Tab 2')

        self.setCentralWidget(self.tabWidget)
        self.setWindowTitle('Text Editor')
        self.show()

    def createPlainTextTab(self):
        plainTextEdit = QPlainTextEdit(self)
        plainTextEdit.textChanged.connect(self.onPlainTextChanged)
        return plainTextEdit

    def createRichTextTab(self):
        textEdit = QTextEdit(self)
        textEdit.textChanged.connect(self.onRichTextChanged)
        return textEdit

    def onPlainTextChanged(self):
        plainTextEdit = self.tabWidget.currentWidget()
        richTextEdit = self.tabWidget.widget(1)

        plainText = plainTextEdit.toPlainText()
        richText = self.convertPlainTextToRichText(plainText)
        richTextEdit.setHtml(richText)

    def onRichTextChanged(self):
        plainTextEdit = self.tabWidget.widget(0)
        richTextEdit = self.tabWidget.currentWidget()

        richText = richTextEdit.toPlainText()
        plainText = self.convertRichTextToPlainText(richText)
        plainTextEdit.setPlainText(plainText)

    def convertPlainTextToRichText(self, plainText):
        richText = plainText.replace("<", "&lt;").replace(">", "&gt;")
        richText = self.applyColorTag(richText)
        return richText

    def convertRichTextToPlainText(self, richText):
        plainText = QTextDocument.toPlainText(QTextDocument(richText))
        return plainText

    def applyColorTag(self, text):
        startTag = "<color=#000000>"
        endTag = "</color>"
        colorStartIndex = text.find(startTag)
        colorEndIndex = text.find(endTag)
        while colorStartIndex != -1 and colorEndIndex != -1:
            color = text[colorStartIndex + len(startTag):colorEndIndex]
            replacementText = f"<span style=\"color:{color};\">"
            text = text.replace(startTag + color + endTag, replacementText, 1)
            colorStartIndex = text.find(startTag)
            colorEndIndex = text.find(endTag)
        return text

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TextEditor()
    sys.exit(app.exec_())
