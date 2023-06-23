def get_section_lines(script):
    section_lines = []
    for line in script:
        parts = line.split(' = ')
        if len(parts) == 2:
            pos, event_data = parts
            event_name = event_data.strip('E "').split(' ')[0]
            if event_name == 'section':
                section_lines.append(line)
    return section_lines

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

def insert_and_sort_sections(script, section_lines):
    script_with_sections = script + section_lines
    sorted_script = sorted(script_with_sections, key=lambda x: int(x.split(' = ')[0]))
    return sorted_script

script = ['768 = E "section Default"', '3840 = E "section Default"', '9984 = E "section Default"', '16080 = E "phrase_start"', '16128 = E "section Verse 1A"', '16224 = E "lyric Ma-"', '16272 = E "lyric chi"', 
          '16320 = E "lyric na-"', '16368 = E "lyric ga-"', '16416 = E "lyric re-"', '16464 = E "lyric ru"', '16512 = E "lyric Hot"', '16608 = E "lyric na"', '16704 = E "lyric Pop"', '16800 = E "lyric Song"', 
          '16896 = E "phrase_start"', '16992 = E "lyric Mo-"', '17040 = E "lyric to-"', '17088 = E "lyric me-"', '17136 = E "lyric ru"', '17184 = E "lyric no"', '17232 = E "lyric wa"', '17280 = E "lyric Heard"', 
          '17376 = E "lyric na"', '17472 = E "lyric Rock"', '17568 = E "lyric Sound"', '17664 = E "phrase_start"', '17760 = E "lyric Shi-"', '17808 = E "lyric ba-"', '17856 = E "lyric ra-"', '17904 = E "lyric re-"', 
          '17952 = E "lyric te-"', '18000 = E "lyric ru"', '18048 = E "lyric you"', '18144 = E "lyric de"', '18192 = E "lyric ji-"', '18240 = E "lyric bun"', '18336 = E "lyric ga"', '18376 = E "phrase_start"',  
          '25104 = E "lyric Ri-"', '25152 = E "lyric setto"', '25248 = E "phrase_start"', '25344 = E "lyric Time"', '25344 = E "section Default"', '25632 = E "lyric to"', '25920 = E "lyric go"', 
          '26112 = E "phrase_start"', '26208 = E "lyric I-"', '26304 = E "lyric ma"', '26400 = E "lyric ko-"', '26496 = E "lyric ko"', '26592 = E "lyric ka-"', '26688 = E "lyric ra"', '26832 = E "phrase_start"', 
          '26880 = E "lyric Go"', '27120 = E "lyric a-"', '27168 = E "lyric way"', '27408 = E "phrase_start"', '27456 = E "lyric Ka-"', '27744 = E "lyric ma-"', '27840 = E "lyric u-"', '27936 = E "lyric na"', 
          '28032 = E "lyric yo-"', '28224 = E "lyric tte"', '28368 = E "phrase_start"', '28416 = E "lyric Be"', '28704 = E "lyric my-"', '28992 = E "lyric self"', '29184 = E "phrase_start"', '29280 = E "lyric Bo-"', 
          '29376 = E "lyric ku"', '29472 = E "lyric wa"', '29568 = E "lyric bo-"', '29664 = E "lyric ku"', '29760 = E "lyric ga"', '29904 = E "phrase_start"', '29952 = E "lyric Don\'t"', '30240 = E "lyric wor-"', 
          '30528 = E "lyric ry"', '30720 = E "phrase_start"', '30816 = E "lyric Hi-"', '30912 = E "lyric to-"', '31008 = E "lyric ri"', '31104 = E "lyric de"', '31200 = E "lyric ii"', '31488 = E "phrase_end"']

section_lines = get_section_lines(script)
remove_section = remove_section_lines(script)
section_back = insert_and_sort_sections(section_lines, remove_section)

# for line in section_lines:
#     print(line)
# print()
# for line in remove_section:
#     print(line)
# print()
# for line in section_back:
#     print(line)

script_lines = ['19200 = E "phrase_start"', '19200 = E "section Default"', '19296 = E "lyric Ku-"', '19344 = E "lyric da-"', '19392 = E "lyric ra-"', '19488 = E "lyric na-"', '19536 = E "lyric i"', '19584 = E "lyric nyuu-"', '19680 = E "lyric su"', '19728 = E "lyric to-"', '19776 = E "lyric bi-"', '19824 = E "lyric kau"', '19920 = E "lyric tsu-"', '19968 = E "lyric ma-"', '20016 = E "lyric ra-"', '20064 = E "lyric nai"', '20112 = E "lyric aha-"', '20160 = E "lyric na-"', '20208 = E "lyric shi"', '20256 = E "lyric yuu-"', '20352 = E "lyric tsu"']

lines = remove_section_lines(script_lines)
print(lines)
