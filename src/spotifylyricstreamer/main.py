from spotifylyricstreamer.LyricManager import LyricManager
from datetime import timedelta

import threading

import time

new_song = False
running = True




def spotify_poller(manager: LyricManager):
    global new_song, running

    current_song_name = None
    while running:
        manager.update_spotify()
        if current_song_name is None:
            current_song_name = manager.current_song.name
        if current_song_name != manager.current_song.name:
            new_song = True
            current_song_name = manager.current_song.name
        time.sleep(5)

        


def time_elapsed(start, now) -> timedelta:
    sec_elapsed = now-start
    return timedelta(seconds=sec_elapsed)

def lyrics_loop(manager: LyricManager):
    global new_song


    while True: # assumes no songs ever skipped, otherwise good

        #put in while true after testing
        #new song
        new_song = False
        manager.update_spotify()
        start = time.monotonic()
        print("NEW SONG: ")
        print(manager.current_song.name)
        print(manager.current_song.artist)

        manager.get_lyrics()
        #find where we are in it right now
        now = time.monotonic()

        base_progress = manager.current_song.progress_td

        current_progress = base_progress + time_elapsed(start=start, now=now)
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


        while not new_song:
            now = time.monotonic()
            current_progress = base_progress + timedelta(seconds=(now - start))

            if current_progress > manager.current_lyrics[current_index+1][0]:
                current_index += 1
                print(manager.current_lyrics[current_index][1])

            if current_index == len(manager.current_lyrics)-1:
                print("END OF SONG")
                break

            time.sleep(0.05)

        time.sleep(((manager.current_song.duration_td - current_progress).total_seconds() + 1))


lyrics_manager = LyricManager()
time.sleep(1) 
poller_manager = LyricManager()

lyrics_manager.update_spotify()
lyrics_manager.get_lyrics()

poller_manager.update_spotify()



api_thread = threading.Thread(target=spotify_poller, daemon=True, args=(poller_manager,))
api_thread.start()

try:
    lyrics_loop(manager=lyrics_manager)
finally:
    running = False
    print("Finished")