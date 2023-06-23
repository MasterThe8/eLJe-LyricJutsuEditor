def remove_section_lines(script):
    filtered_script = []
    for line in script:
        parts = line.split(' = ')
        if len(parts) == 2:
            event_name = parts[1].strip('E "').split(' ')[0]
            if event_name != 'section':
                filtered_script.append(line)
        else:
            filtered_script.append(line)
    return filtered_script

def find_first_lyric_element(lyric_items):
    first_lyric_element = None
    for item in lyric_items:
        if 'lyric' in item:
            first_lyric_element = item
            lyric_items.remove(item)
            break
    return first_lyric_element

def find_last_lyric_element(lyric_items):
    last_lyric_element = None
    for item in reversed(lyric_items):
        if 'lyric' in item:
            last_lyric_element = item
            lyric_items.remove(item)
            break
    return last_lyric_element

def split_lyric(lyric):
    parts = lyric.split(' = E "lyric ')
    position = int(parts[0])
    lyric_value = parts[1].strip('"')
    return position, lyric_value

def get_lyric_item(events):
    lines_temp = []
    for line in events[1:]:
        pos, event_data = line.split(' = ')
        event_name, *value = event_data.strip('E "').split(' ')
        value = ' '.join(value)
        if event_name != 'section':
            lines_temp.append(value)
    return lines_temp

def convert_list_to_string(lyric_items):
    result = ''
    for i, item in enumerate(lyric_items):
        if i > 0 and not lyric_items[i-1].endswith('-'):
            result += ' '
        result += item.rstrip('-')
    return result

def insert_and_sort(script, element):
    if isinstance(element, list):
        script.extend(element)
    elif isinstance(element, str):
        script.append(element)

    sorted_script = sorted(script, key=lambda x: int(x.split(' = ')[0]))
    return sorted_script

def apply_lyric_color(lyric, pos, syllable):
    result = []
    hex_color = "#fca101"
    
    if '-' in syllable:
        line1 = str(int(pos) - 4) + " = E \"lyric " + lyric + "\""
        line2 = str(int(pos) - 3) + " = E \"phrase_start\""
        line3 = str(int(pos) - 2) + " = E \"lyric -\""
        line4 = str(int(pos) - 1) + " = E \"phrase_start\""
        line5 = str(int(pos)) + " = E \"lyric <color=#FFFFFF><color=" + hex_color + "> " + syllable + "\""
    else:
        line1 = str(int(pos) - 4) + " = E \"lyric " + lyric + "\""
        line2 = str(int(pos) - 3) + " = E \"phrase_start\""
        line3 = str(int(pos) - 2) + " = E \"lyric -\""
        line4 = str(int(pos) - 1) + " = E \"phrase_start\""
        line5 = str(int(pos)) + " = E \"lyric <color=#FFFFFF><color=" + hex_color + "> " + syllable + " " + "\""
        
    result.append(line1)
    result.append(line2)
    result.append(line3)
    result.append(line4)
    result.append(line5)
    return result

def apply_lyric_close(pos, syllable):
    last_phrase = str(int(pos)) + " = E \"lyric " + syllable + "</color></color>"
    return last_phrase

# ================================================

script_lines = ['19200 = E "phrase_start"', '19200 = E "section Default"', '19296 = E "lyric Ku-"', '19344 = E "lyric da-"', '19392 = E "lyric ra-"', '19488 = E "lyric na-"', '19536 = E "lyric i"', '19584 = E "lyric nyuu-"', '19680 = E "lyric su"', '19728 = E "lyric to-"', '19776 = E "lyric bi-"', '19824 = E "lyric kau"', '19920 = E "lyric tsu-"', '19968 = E "lyric ma-"', '20016 = E "lyric ra-"', '20064 = E "lyric nai"', '20112 = E "lyric aha-"', '20160 = E "lyric na-"', '20208 = E "lyric shi"', '20256 = E "lyric yuu-"', '20352 = E "lyric tsu"']

lines = remove_section_lines(script_lines)
print("lines : ", lines)
print()
first_lyric = find_first_lyric_element(lines)
print("First Lyric : ", first_lyric)
print()
last_lyric = find_last_lyric_element(lines)
print("last Lyric : ", last_lyric)
print()
first_pos, first_value = split_lyric(first_lyric)
print(first_pos, first_value)
print()
last_pos, last_value = split_lyric(last_lyric)
print(last_pos, last_value)
print()

# ================================================

lyric_items = get_lyric_item(script_lines)
print("Lyric Items : ", lyric_items)
print()
lyric = convert_list_to_string(lyric_items)
print("Lyric : ", lyric)
print()

# ================================================

first_phrase = apply_lyric_color(lyric, first_pos, first_value)
for i in first_phrase:
    print(i)
print()
last_phrase = apply_lyric_close(last_pos, last_value)
print("Last Phrase :\n" + last_phrase)
print()

# ================================================

print("Lines : ", lines)
print()
lines = insert_and_sort(lines, first_phrase)
lines = insert_and_sort(lines, last_phrase)
print("Lines : ", lines)
print()

for i in lines:
    print(i)


