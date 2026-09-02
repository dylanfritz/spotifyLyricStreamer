from spotifylyricstreamer.LyricManager import LyricManager
from datetime import timedelta

import threading
import time

running = True
new_song_event = threading.Event()
state_lock = threading.Lock()


shared_song_name = None


def spotify_poller(manager: LyricManager):
    global shared_song_name, running

    while running:
        with state_lock:
            manager.update_spotify()
            name = manager.current_song.name

        if shared_song_name is None:
            shared_song_name = name
        elif name != shared_song_name:
            shared_song_name = name
            new_song_event.set()

        time.sleep(5)


def time_elapsed(start, now) -> timedelta:
    return timedelta(seconds=now - start)


def lyrics_loop(manager: LyricManager):
    global shared_song_name

    while running:
        new_song_event.clear()

        with state_lock:
            manager.update_spotify()
            shared_song_name = manager.current_song.name
            base_progress = manager.current_song.progress_td
            duration = manager.current_song.duration_td
            start = time.monotonic()  # taken atomically with base_progress

        print("NEW SONG: ")
        print(manager.current_song.name)
        print(manager.current_song.artist)

        manager.get_lyrics()

        # Where are we right now, using ONLY our own snapshot + elapsed time
        now = time.monotonic()
        current_progress = base_progress + time_elapsed(start, now)
        current_index = 0

        if manager.current_lyrics is None:
            print("COULD NOT FIND LYRICS. NO DISPLAY.")
            wait = (duration - current_progress).total_seconds() + 1.5
            new_song_event.wait(timeout=max(wait, 0))
            continue

        for i, (ts, _) in enumerate(manager.current_lyrics):
            if ts > current_progress:
                current_index = max(0, i - 1)
                break

        print(manager.current_lyrics[current_index][1])

        while not new_song_event.is_set():
            now = time.monotonic()
            current_progress = base_progress + time_elapsed(start, now)

            next_index = current_index + 1
            if (next_index < len(manager.current_lyrics)
                    and current_progress > manager.current_lyrics[next_index][0]):
                current_index = next_index
                print(manager.current_lyrics[current_index][1])

            if current_index == len(manager.current_lyrics) - 1:
                print("END OF SONG")
                break

            time.sleep(0.05)

        if not new_song_event.is_set():
            remaining = (duration - current_progress).total_seconds() + 1
            new_song_event.wait(timeout=max(remaining, 0))


manager = LyricManager()

api_thread = threading.Thread(target=spotify_poller, daemon=True, args=(manager,))
api_thread.start()

try:
    lyrics_loop(manager=manager)
finally:
    running = False
    print("Finished")