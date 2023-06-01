lines = ['li-', 'mat', 'Li-', 'rik']
script = {
    14: 'E "lyric <color=#FF0000>Ka</color>"',
    18: 'E "lyric <i></i>"',
    19: 'E "phrase_start"',
    20: 'E "lyric <color=#FF0000>Kali</color>"',
    30: 'E "lyric <i></i>"',
    31: 'E "phrase_start"',
    32: 'E "lyric <color=#FF0000>Kalimat</color>"',
    34: 'E "lyric <i></i>"',
    35: 'E "phrase_start"',
    38: 'E "lyric <color=#FF0000>Kalimat Li</color>"',
    40: 'E "lyric <i></i>"',
    41: 'E "phrase_start"',
    42: 'E "lyric <color=#FF0000>Kalimat Lirik</color>"'
}

temp_lyric = lines.copy()
value_to_insert = []
color_values = []

# Remove '- ' in lyric
for i in range(len(temp_lyric)):
    temp = ' '.join(temp_lyric[i:])
    result = ''.join(temp).replace('- ', '')
    value_to_insert.append(result)

# Get line with </color>
for key, value in script.items():
    if "</color>" in value:
        color_values.append(value)

length_value_to_insert = len(value_to_insert)
length_color_values = len(color_values)

# Replace </color> with </color>+lyric
for i in range(length_color_values - 1):
    if i < length_value_to_insert:
        color_values[i] = color_values[i].replace('</color>', f'</color>{value_to_insert[i]}')

# Mengembalikan nilai color_values ke dalam script
for i, key in enumerate(script):
    if "</color>" in script[key]:
        script[key] = color_values.pop(0)
        
for i,j in script.items():
    print(f'{i} = {j}')