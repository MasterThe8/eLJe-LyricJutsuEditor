def process_lyrics(events):
    lines = []
    counts = []
    current_line = ''
    current_line_positions = []
    for event in events:
        pos, event_data = event.split(' = ')
        event_name, *value = event_data.strip('E "').split(' ')
        value = ' '.join(value)
        
        if event_name == 'phrase_start':
            if current_line:
                lines.append(current_line.strip())
                counts.append(len(current_line_positions))
                current_line = ''
                current_line_positions = []
        elif event_name == 'lyric':
            if '-' in value:
                if current_line and not current_line.endswith('-'):
                    current_line += ' '
                current_line += value
            else:
                current_line += ' ' + value
            current_line_positions.append(pos)
    
    if current_line:
        lines.append(current_line.strip())
        counts.append(len(current_line_positions))
    
    return lines, counts


# Contoh penggunaan
events = [
    '120 = E "phrase_start"',
    '123 = E "lyric Satu"',
    '125 = E "phrase_start"',
    '128 = E "lyric Du-"',
    '130 = E "lyric a"',
    '132 = E "lyric Ti-"',
    '134 = E "lyric ga"',
    '145 = E "phrase_start"',
    '150 = E "lyric Empat"',
    '154 = E "lyric Lima"',
]

lyrics, lyric_counts = process_lyrics(events)

lyrics_output = '\n'.join(f'{line} ({count})' for line, count in zip(lyrics, lyric_counts))
script_output = '\n'.join(events)

print(lyrics_output)
print()
print(script_output)
