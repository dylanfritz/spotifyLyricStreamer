from spotifylyricstreamer.LyricManager import LyricManager
from datetime import timedelta

import time



manager = LyricManager()
manager.update_spotify()
manager.get_lyrics()


def time_elapsed(start, now) -> timedelta:
    sec_elapsed = now-start
    return timedelta(seconds=sec_elapsed)


while True: # assumes no songs ever skipped, otherwise good

    #put in while true after testing
    #new song
    manager.update_spotify()
    start = time.monotonic()
    print("NEW SONG: ")
    print(manager.current_song.name)
    print(manager.current_song.artist)

    manager.get_lyrics()
    #find where we are in it right now
    now = time.monotonic()

    current_progress = manager.current_song.progress_td + time_elapsed(start=start, now=now)
    current_index = 0 

    if manager.current_lyrics is None:
        print("COULD NOT FIND LYRICS. NO DISPLAY.")
        time.sleep((manager.current_song.duration_td - current_progress).total_seconds() + 1.5)
        continue
    
    
    for i, (ts, _) in enumerate(manager.current_lyrics):
        if ts > current_progress:
            current_index = max(0, i - 1)
            break   

    print(manager.current_lyrics[current_index][1])


    while True:
        now = time.monotonic()
        current_progress = manager.current_song.progress_td + timedelta(seconds=(now - start))

        if current_progress > manager.current_lyrics[current_index+1][0]:
            current_index += 1
            print(manager.current_lyrics[current_index][1])

        if current_index == len(manager.current_lyrics)-1:
            print("END OF SONG")
            break

        time.sleep(0.05)

    time.sleep((manager.current_song.duration_td - current_progress).total_seconds() + 1)
