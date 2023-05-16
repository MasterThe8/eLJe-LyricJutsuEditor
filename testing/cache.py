        # Melakukan iterasi untuk mencari tag dan menerapkan format ke teks
        while currentIndex < len(plainText):
            # Mencari tag <color=...>
            colorStartIndex = plainText.find(colorStartTag, currentIndex)
            if colorStartIndex != -1:
                colorEndIndex = plainText.find(">", colorStartIndex)
                if colorEndIndex != -1:
                    colorValue = plainText[colorStartIndex + len(colorStartTag):colorEndIndex]
                    currentIndex = colorEndIndex + 1

                    # Mengatur format warna teks
                    colorFormat = QTextCharFormat()
                    colorFormat.setForeground(Qt.black)  # Warna default jika tidak ditemukan
                    colorFormat.setForeground(Qt.black)  # Warna default jika tidak ditemukan
                    try:
                        colorFormat.setForeground(Qt.black if colorValue == "#000000" else QColor(colorValue))
                    except:
                        pass

                    cursor.mergeCharFormat(colorFormat)

            # Mencari tag <b>
            elif plainText.find(boldStartTag, currentIndex) == currentdef convertHTMLToRichText(self, plainText):
    rich_text = ""
    color_format = QTextCharFormat()
    
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
        else:
            color_start_index = c_start_index + 8
            color_end_index = plainText.find(">", color_start_index)
            color_value = plainText[color_start_index : color_end_index]
            text = plainText[index + 7 : c_start_index]
            
            color_format.setForeground(QColor(color_value))
            rich_text += "<span style='color: {};'>{}</span>".format(color_value, text)
            
            plainText = plainText[color_end_index + 1:]
        
        start_index = plainText.find("<b>")
        end_index = plainText.find("</b>")
        i_start_index = plainText.find("<i>")
        i_end_index = plainText.find("</i>")
        c_start_index = plainText.find("<color=")
        c_end_index = plainText.find("</color>")
    
    rich_text += plainText
    return rich_text
Index:
                boldEndIndex = plainText.find(boldEndTag, currentIndex)
                if boldEndIndex != -1:
                    currentIndex = boldEndIndex + len(boldEndTag)

                    # Mengatur format teks tebal
                    boldFormat = QTextCharFormat()
                    boldFormat.setFontWeight(QFont.Bold)
                    cursor.mergeCharFormat(boldFormat)

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
                    plainText.find(colorStartTag, currentIndex),
                    plainText.find(boldStartTag, currentIndex),
                    plainText.find(italicStartTag, currentIndex)
                )

                if nextTagIndex == -1:
                    nextTagIndex = len(plainText)

                # Menambahkan teks biasa
                text = plainText[currentIndex:nextTagIndex]
                cursor.insertText(text, defaultFormat)
                currentIndex = nextTagIndex