def get_lines(events, position):
    lines = []
    current_line = ''
    current_position = None

    for event in events:
        pos, event_data = event.split(' = ')
        event_name, *value = event_data.strip('E "').split(' ')
        value = ' '.join(value)
        
        if current_position == position:
            lines.append(current_line)
        
        if pos == position:
            current_position = pos
            current_line = event
        elif event_name == 'phrase_start':
            current_position = None

        if current_position is not None and pos != position:
            current_line = event

    if current_position == position:
        lines.append(current_line)

    return lines

events = [
    '1 = E "phrase_start"',
    '2 = E "lyric Sa-"',
    '6 = E "lyric tu"',
    '10 = E "phrase_start"',
    '12 = E "lyric Ka-"',
    '18 = E "lyric li-"',
    '30 = E "lyric mat"',
    '41 = E "phrase_start"',
    '44 = E "lyric Li-"',
    '48 = E "lyric rik"',
]

position = '12'
lines = get_lines(events, position)

temp_lines = lines.copy()

def cc(lines):
    result = []
    previous_lyric = ''
    temp = lines[:]
    
    for line in lines:
        pos, event_data = line.split(' = ')
        event_name, *value = event_data.strip('E "').split(' ')
        value = ' '.join(value)
        lyric = ''.join([str(element) for element in value if element != '-'])
        hex = '#FF0000'

        line1 = str(int(pos)) + " = E \"lyric <i></i>\""
        line2 = str(int(pos) + 1) + " = E \"phrase_start\""
        line3 = str(int(pos) + 2) + " = E \"lyric <color=" + hex + ">" + previous_lyric + lyric + "</color>\""
        line = line1 + '\n' + line2 + '\n' + line3
        
        result.append(line)
        previous_lyric += lyric
    return result

result = cc(lines)
result_split = [line for i in result for line in i.split('\n')]

def get_lyric_item(events):
    lines_temp = []
    for line in events[1:]:
        pos, event_data = line.split(' = ')
        event_name, *value = event_data.strip('E "').split(' ')
        value = ' '.join(value)
        lines_temp.append(value)
    return lines_temp

lyric_items = get_lyric_item(lines)

def add_next_lyric(lines, script):
    script_temp = {int(item.split(' = ')[0]): item.split(' = ')[1] for item in script}

    temp_lyric = lines.copy()
    value_to_insert = []
    color_values = []
    
    # Remove '- ' in lyric
    for i in range(len(temp_lyric)):
        temp = ' '.join(temp_lyric[i:])
        result = ''.join(temp).replace('- ', '')
        value_to_insert.append(result)

    # Get line with </color>
    for key, value in script_temp.items():
        if "</color>" in value:
            color_values.append(value)

    length_value_to_insert = len(value_to_insert)
    length_color_values = len(color_values)

    # Replace </color> with </color>+lyric
    for i in range(length_color_values - 1):
        if i < length_value_to_insert:
            color_values[i] = color_values[i].replace('</color>', f'</color>{value_to_insert[i]}')

    # Mengembalikan nilai color_values ke dalam script
    for i, key in enumerate(script_temp):
        if "</color>" in script_temp[key]:
            script_temp[key] = color_values.pop(0)

    # for i,j in script_temp.items():
    #     print(f'{i} = {j}')
        
    script_result = [f"{key} = {value}" for key, value in script_temp.items()]

    return script_result

# add_next_lyric(lyric_items, result_split)
last_result = add_next_lyric(lyric_items, result_split)


index = next((i for i, event in enumerate(events) if event.startswith(position + ' = ')), None)

if index is not None:
    del events[index]

    events[index:index] = last_result

# Pengecekan dan penghapusan baris dengan nomor yang sama
existing_numbers = set()
i = 0
while i < len(events):
    event_parts = events[i].split(' = ')
    if len(event_parts) >= 2:
        event_number = event_parts[0]
        if event_number in existing_numbers:
            del events[i]
            continue
        else:
            existing_numbers.add(event_number)
    i += 1


for event in events:
    print(event)
        
