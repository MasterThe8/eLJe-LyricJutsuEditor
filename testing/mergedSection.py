def merge_and_sort(script, section_lines):
    lines = script.split('\n')
    merged_lines = lines + section_lines
    merged_lines.sort(key=lambda x: int(x.split(' = ')[0]) if x else float('inf'))
    merged_script = '\n'.join(merged_lines)
    return merged_script

def remove_duplicates(script):
    lines = script.split('\n')
    existing_lines = set()

    deduplicated_lines = []
    for line in lines:
        if line not in existing_lines:
            deduplicated_lines.append(line)
            existing_lines.add(line)

    deduplicated_script = '\n'.join(deduplicated_lines)
    return deduplicated_script

script = '''
12 = E "phrase_start"
15 = E "lyric Ka-"
25 = E "lyric li-"
34 = E "lyric mat"
46 = E "lyric waw1"
46 = E "phrase_start"
46 = E "section Main Theme 1"
52 = E "lyric Li-"
61 = E "lyric rik"
83 = E "lyric La-"
88 = E "lyric gu"
91 = E "section Pre-Chorus 1A"
91 = E "lyric waw2"
'''

section_lines = [
    '10 = E "section Chorus 1B"',
    '46 = E "section Main Theme 1"',
    '78 = E "section Verse 1A"',
    '91 = E "section Pre-Chorus 1A"',
]

merged_script = merge_and_sort(script, section_lines)
print(merged_script, "\n\n")

removedup = remove_duplicates(merged_script)
print(removedup)
