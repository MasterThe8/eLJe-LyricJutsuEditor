def process_lyrics(events):
    lines = []
    current_line = ''
    current_line_positions = []
    for event in events:
        pos, event_data = event.split(' = ')
        event_name, *value = event_data.strip('E "').split(' ')
        value = ' '.join(value)
        
        if event_name == 'phrase_start':
            if current_line:
                lines.append((current_line.strip(), len(current_line_positions)))
                current_line = ''
                current_line_positions = []
        elif event_name == 'lyric':
            if '-' in value:
                if current_line and not current_line.endswith('-'):
                    current_line += ' '
                current_line += value
            else:
                if current_line and not current_line.endswith('-'):
                    current_line += ' '
                current_line += '' + value
            current_line_positions.append(pos)
    
    if current_line:
        lines.append((current_line.strip(), len(current_line_positions)))
    
    return lines

events = [
    '120 = E "phrase_start"',
    '123 = E "lyric Satu"',
    '125 = E "phrase_start"',
    '128 = E "lyric Du-"',
    '130 = E "lyric a-"',
    '132 = E "lyric Ti-"',
    '134 = E "lyric ga"',
    '136 = E "lyric e-"',
    '137 = E "lyric m"',
    '138 = E "lyric p-"',
    '139 = E "lyric a-"',
    '140 = E "lyric t"',
    '145 = E "phrase_start"',
    '150 = E "lyric Lima"',
    '154 = E "lyric Enam"',
]

# lyrics = process_lyrics(events)
# for line, count in lyrics:
#     print(f"{line} ({count})")

print(process_lyrics(events))