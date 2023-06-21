def get_section_lines(script):
    section_lines = []
    lines = script.split('\n')
    for line in lines:
        parts = line.split(' = ')
        if len(parts) == 2:
            pos, event_data = parts
            event_name = event_data.strip('E "').split(' ')[0]
            if event_name == 'section':
                section_lines.append(line)
    return section_lines

script = '''
10 = E "section Chorus 1B"
12 = E "phrase_start"
15 = E "lyric Ka-"
25 = E "lyric li-"
34 = E "lyric mat"
46 = E "section Main Theme 1"
52 = E "lyric Li-"
61 = E "lyric rik"
78 = E "section Verse 1A"
83 = E "lyric La-"
88 = E "lyric gu"
91 = E "section Pre-Chorus 1A"
'''

section_lines = get_section_lines(script)

print(section_lines, "\n")

for line in section_lines:
    print(line)
