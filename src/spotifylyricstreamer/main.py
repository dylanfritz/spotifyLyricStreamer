from spotifylyricstreamer.LyricManager import LyricManager
from datetime import timedelta

import threading
import time

running = True
new_song_event = threading.Event()
state_lock = threading.Lock()


def spotify_poller(manager: LyricManager):
    global running

    known_name = None
    while running:
        with state_lock:
            manager.update_spotify()
            name = manager.current_song.name

        if known_name is None or name != known_name:
            known_name = name
            new_song_event.set()

        time.sleep(5)


def time_elapsed(start, now) -> timedelta:
    return timedelta(seconds=now - start)


def lyrics_loop(manager: LyricManager):
    while running:
        new_song_event.wait()
        new_song_event.clear()

        with state_lock:
            song = manager.current_song
            manager.get_lyrics()
            lyrics = manager.current_lyrics
            base_progress = song.progress_td
            duration = song.duration_td
            start = time.monotonic()

        print("NEW SONG: ")
        print(song.name)
        print(song.artist)

        if lyrics is None:
            print("COULD NOT FIND LYRICS. NO DISPLAY.")
            wait = (duration - base_progress).total_seconds() + 1.5
            new_song_event.wait(timeout=max(wait, 0))
            continue

        current_progress = base_progress
        current_index = 0
        for i, (ts, _) in enumerate(lyrics):
            if ts > current_progress:
                current_index = max(0, i - 1)
                break

        print(lyrics[current_index][1])

        while not new_song_event.is_set():
            now = time.monotonic()
            current_progress = base_progress + time_elapsed(start, now)

            next_index = current_index + 1
            if next_index < len(lyrics) and current_progress > lyrics[next_index][0]:
                current_index = next_index
                print(lyrics[current_index][1])

            if current_index == len(lyrics) - 1:
                print("END OF SONG")
                break

            time.sleep(0.05)


manager = LyricManager()

api_thread = threading.Thread(target=spotify_poller, daemon=True, args=(manager,))
api_thread.start()

try:
    lyrics_loop(manager=manager)
finally:
    running = False
    print("Finished")