events_all = []
events_phrase_array = []

def read_and_modify_events():
    temp_event_array = events_all.copy()
    events_phrase_array = []
    temp_phrase_start_ticks = []
    temp_phrase_end_ticks = []
    temp_phrase_start_indexes = []
    temp_phrase_end_indexes = []

    for i in range(len(temp_event_array) - 1, -1, -1):
        if " = E \"phrase_start\"" not in temp_event_array[i] and " = E \"phrase_end\"" not in temp_event_array[i] and " = E \"lyric \"" not in temp_event_array[i]:
            temp_event_array.pop(i)
        elif " = E \"phrase_start\"" in temp_event_array[i]:
            temp_phrase_start_ticks.append(temp_event_array[i].split("=")[0].strip())
        elif " = E \"phrase_end\"" in temp_event_array[i]:
            temp_phrase_end_ticks.append(temp_event_array[i].split("=")[0].strip())

    temp_phrase_start_ticks.reverse()
    temp_phrase_end_ticks.reverse()
    start_count = 0

    for i in range(len(temp_event_array)):
        temp_start_tick = int(temp_phrase_start_ticks[start_count])
        temp_event_tick = int(temp_event_array[i].split("=")[0].strip())

        if temp_start_tick == temp_event_tick and "phrase_start" not in temp_event_array[i] and "phrase_start" in temp_event_array[i + 1]:
            temp = temp_event_array.pop(i + 1)
            temp_event_array.insert(i, temp)
            start_count += 1
        elif temp_start_tick < temp_event_tick and "phrase_start" not in temp_event_array[i] and "phrase_end" not in temp_event_array[i]:
            start_count += 1

    for i in range(len(temp_event_array)):
        if " = E \"phrase_start\"" in temp_event_array[i]:
            temp_phrase_start_indexes.append(i)
        elif " = E \"phrase_end\"" in temp_event_array[i]:
            temp_phrase_end_indexes.append(i)

    ends_used = 0

    for i in range(len(temp_phrase_start_indexes)):
        if temp_phrase_start_indexes[i + 1] > temp_phrase_end_indexes[ends_used] or temp_phrase_start_indexes[i + 1] == None:
            events_phrase_array.append(temp_event_array[temp_phrase_start_indexes[i] + 1:temp_phrase_end_indexes[ends_used]])
            ends_used += 1
        else:
            events_phrase_array.append(temp_event_array[temp_phrase_start_indexes[i] + 1:temp_phrase_start_indexes[i + 1]])

    lyric_count = sum(len(phrase) for phrase in events_phrase_array)
    return lyric_count

def get_lyrics_from_chart():
    lyrics_per_phrase = []

    if len(events_phrase_array) == 0:
        print("No lyric events found form the chart")
    else:
        for i in range(len(events_phrase_array)):
            temp_string = ""
            for j in range(len(events_phrase_array[i])):
                temp = events_phrase_array[i][j].split("lyric ")[1]
                temp = temp[:-1]
                if temp.endswith("-") or temp.endswith("="):
                    temp_string += temp
                else:
                    temp_string += temp + " "
            lyrics_per_phrase.append(temp_string.strip())

    return "\n".join(lyrics_per_phrase)
