def convert_list_to_string(lyric_items):
    result = ''
    for i, item in enumerate(lyric_items):
        if i > 0 and not lyric_items[i-1].endswith('-'):
            result += ' '
        result += item.rstrip('-')
    return result

lyric_items = ['Ma-', 'chi', 'na-', 'ga-', 're-', 'ru', 'Hot', 'na', 'Pop', 'Song']

lyric = convert_list_to_string(lyric_items)

print(lyric)

# ['19200 = E "phrase_start"', '19200 = E "section Default"', '19296 = E "lyric Ku-"', '19344 = E "lyric da-"', '19392 = E "lyric ra-"', '19488 = E "lyric na-"', '19536 = E "lyric i"', '19584 = E "lyric nyuu-"', '19680 = E "lyric su"', '19728 = E "lyric to-"', '19776 = E "lyric bi-"', '19824 = E "lyric kau"', '19920 = E "lyric tsu-"', '19968 = E "lyric ma-"', '20016 = E "lyric ra-"', '20064 = E "lyric nai"', '20112 = E "lyric aha-"', '20160 = E "lyric na-"', '20208 = E "lyric shi"', '20256 = E "lyric yuu-"', '20352 = E "lyric tsu"']