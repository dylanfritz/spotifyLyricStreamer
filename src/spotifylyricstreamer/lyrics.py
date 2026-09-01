import re
import traceback
from datetime import timedelta
import syncedlyrics


def get_timestamp_lyric(lyrics, timestamp:timedelta):
    for i, (lyric_timestamp, lyric) in enumerate(lyrics):
        if lyric_timestamp > timestamp:
            return (i-1, lyrics[i-1][1])
    return (i-1, "")

def str_to_timestamp(timestamp_str):
    timestamp_str = timestamp_str.replace("[","").replace("]","").replace(".", ":")

    minutes, seconds, centiseconds = map(int, timestamp_str.split(':'))

    timestamp = timedelta(minutes=minutes, seconds=seconds, milliseconds=centiseconds*10)

    return timestamp

def parse_lrc(lrc_string:str):

    if lrc_string is None:
        return None
    TIMESTAMP_REGEX = "\\[[^\\]]*\\]"
    pattern = re.compile(TIMESTAMP_REGEX)

    parsed_lyrcs = []

    try:
        if "\n" in lrc_string:
            # Separate lines format

            for line in lrc_string.split("\n"):
                match_ = pattern.search(line)

                if match_ == None:
                    continue
                
                timestamp_str = match_.group()

                # >>> FIX: skip non-timestamp tags like [Intro], [ti:...], [ar:...]
                ts_clean = timestamp_str.replace("[","").replace("]","").replace(".", ":")
                parts = ts_clean.split(":")
                if not all(p.isdigit() for p in parts):
                    continue
                # <<< END FIX

                timestamp = str_to_timestamp(timestamp_str)

                lyric = line.replace(match_.group(), "").strip()

                #Added feature request by mene
                #Empty lines in lyrics are replaced by a different character
                if lyric == "":
                    lyric = "[]"

                parsed_lyrcs.append((timestamp, lyric))
        
        else:
            # No line break format
            
            matches = pattern.finditer(lrc_string)

            str_indexes = []
            timestamps = [timedelta(milliseconds=0)]

            for match_ in matches:
                str_indexes.append(match_.span()[0])

                timestamp_str = match_.group()

                # >>> FIX: skip non-timestamp tags
                ts_clean = timestamp_str.replace("[","").replace("]","").replace(".", ":")
                parts = ts_clean.split(":")
                if not all(p.isdigit() for p in parts):
                    continue
                # <<< END FIX

                timestamps.append(str_to_timestamp(timestamp_str))

            c_index = 0

            for i, index in enumerate(str_indexes):
                lyric = lrc_string[c_index:index].strip()
                timestamp = timestamps[i]

                c_index = index + 10

                parsed_lyrcs.append((timestamp, lyric))

    except Exception:
        print(traceback.format_exc())
        return None
        
    return (None if parsed_lyrcs == [] else parsed_lyrcs)

def fetch_lrc(song_name:str, artist:str, allow_plain_format=False):
    search_term = song_name+" "
    if type(artist) is list:
        search_term += artist[0]
    elif type(artist) is str:
        search_term += artist

    return syncedlyrics.search(search_term=search_term)

def fetch_parsed_lyrics(song_name:str, artist:str, allow_plain_format=False):
    return parse_lrc(fetch_lrc(song_name=song_name, artist=artist))
