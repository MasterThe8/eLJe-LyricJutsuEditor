# lines = ['12 = E "lyric Ka-"', '18 = E "lyric li-"', '30 = E "lyric mat"', '32 = E "lyric Li-"', '35 = E "lyric rik"']
# lines = ['12 = E "lyric <i></i>"',
# '13 = E "phrase_start"',
# '14 = E "lyric <color=#FF0000>Ka</color>"',
# '18 = E "lyric <i></i>"',
# '19 = E "phrase_start"',
# '20 = E "lyric <color=#FF0000>Kali</color>"',
# '30 = E "lyric <i></i>"',
# '31 = E "phrase_start"',
# '32 = E "lyric <color=#FF0000>Kalimat</color>"']

lines = ['14 = E "lyric <color=#FF0000>Ka</color>"', '20 = E "lyric <color=#FF0000>Kali</color>"', '32 = E "lyric <color=#FF0000>Kalimat</color>"']

result = []

# Get lyric in line
for line in lines[1:]:
    pos, event_data = line.split(' = ')
    event_name, *value = event_data.strip('E "').split(' ')
    value = ' '.join(value)
    result.append(value)
    # if value.endswith('-'):
    #     lyric_temp += value
    # else:
    #     lyric = lyric_temp + value
    #     result.append(lyric)
    #     lyric_temp = ''

print(result)