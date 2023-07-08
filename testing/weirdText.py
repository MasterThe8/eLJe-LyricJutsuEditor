import codecs

def convertText(path, text):
    input = text
    result = ""
    
    with codecs.open(path, "r", "utf-8") as file:
        list_text = file.read()
    
    char_len = len(list_text)
    
    if char_len == 26:
        char_list = list(list_text)
    else:
        x = char_len // 26
        char_list = [list_text[i:i+x] for i in range(0, len(list_text), x)]
        
    for char in input:
        if char.isalpha():
            index = ord(char.upper()) - ord('A')
            if index >= 0 and index < len(char_list):
                result += char_list[index]
        else:
            result += char
            
    return result

text_input = "test"
t = "weird_text/wt"
path_list = []

for i in range (1, 27):
    path_file = "{}{}".format(t,i)
    path_list.append(path_file)
    for path in path_list:
        result = convertText(path, text_input)
        print(result+'\n')