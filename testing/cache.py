import codecs

with codecs.open("symbols/sym", "r", "utf-8") as file:
    symbols = file.read()

print(len(symbols))

# Emoticon : 27
# Letters : 97
# Math : 159
# Shape : 275
# Symbol : 182

count = 27 + 97 + 159 + 275 + 182
print(count)