    def convertPlainTextToRichText(self, plainText):
        textEdit = self.tabRichTextEdit()
        cursor = textEdit.textCursor()
        cursor.beginEditBlock()

        # Mengatur format awal teks
        defaultFormat = cursor.charFormat()
        
        boldStartTag = "<b>"
        boldEndTag = "</b>"
        italicStartTag = "<i>"
        italicEndTag = "</i>"

        currentIndex = 0
        
        # Melakukan iterasi untuk mencari tag dan menerapkan format ke teks
        while currentIndex < len(plainText):
            # Mencari tag <b>
            if plainText.find(boldStartTag, currentIndex) == currentIndex:
                boldEndIndex = plainText.find(boldEndTag, currentIndex)
                if boldEndIndex != -1:
                    # Menerapkan format teks tebal
                    cursor.setPosition(currentIndex + len(boldStartTag), QTextCursor.MoveAnchor)
                    cursor.setPosition(boldEndIndex, QTextCursor.KeepAnchor)
                    boldFormat = QTextCharFormat()
                    boldFormat.setFontWeight(QFont.Bold)
                    cursor.mergeCharFormat(boldFormat)
                    currentIndex = boldEndIndex + len(boldEndTag)

            # Mencari tag <i>
            elif plainText.find(italicStartTag, currentIndex) == currentIndex:
                italicEndIndex = plainText.find(italicEndTag, currentIndex)
                if italicEndIndex != -1:
                    currentIndex = italicEndIndex + len(italicEndTag)

                    # Mengatur format teks miring
                    italicFormat = QTextCharFormat()
                    italicFormat.setFontItalic(True)
                    cursor.mergeCharFormat(italicFormat)

            # Teks biasa
            else:
                # Menemukan teks berikutnya yang mengandung tag
                nextTagIndex = min(
                    plainText.find(boldStartTag, currentIndex),
                    plainText.find(italicStartTag, currentIndex)
                )

                if nextTagIndex == -1:
                    nextTagIndex = len(plainText)

                # Menambahkan teks biasa
                text = plainText[currentIndex:nextTagIndex]
                cursor.insertText(text, defaultFormat)
                currentIndex = nextTagIndex

        cursor.endEditBlock()
        richText = textEdit.toHtml()

        return richText