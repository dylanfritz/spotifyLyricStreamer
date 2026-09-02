from spotifylyricstreamer.LyricManager import LyricManager
from datetime import timedelta

import asyncio

import time

song_changed = False

async def spotify_watcher(manager: LyricManager):
    global song_changed

    last_song = None

    while True:
        manager.update_spotify()
        current_song_name = manager.current_song.name

        if last_song is None:
            last_song = current_song_name

        if current_song_name != last_song:
            song_changed = True
            last_song = current_song_name

        await asyncio.sleep(5)



def time_elapsed(start, now) -> timedelta:
    sec_elapsed = now-start
    return timedelta(seconds=sec_elapsed)

async def lyric_loop(manager: LyricManager):
    global song_changed

    while True: # assumes no songs ever skipped, otherwise good
        #new song
        # manager.update_spotify()
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
            await asyncio.sleep((manager.current_song.duration_td - current_progress).total_seconds() + 1.5)
            continue
        
        
        for i, (ts, _) in enumerate(manager.current_lyrics):
            if ts > current_progress:
                current_index = max(0, i - 1)
                break   

        print(manager.current_lyrics[current_index][1])


        while not song_changed:
            now = time.monotonic()
            current_progress = manager.current_song.progress_td + timedelta(seconds=(now - start))

            if current_progress > manager.current_lyrics[current_index+1][0]:
                current_index += 1
                print(manager.current_lyrics[current_index][1])

            if current_index == len(manager.current_lyrics)-1:
                print("END OF SONG")
                break

            await asyncio.sleep(0.05)

        await asyncio.sleep((manager.current_song.duration_td - current_progress).total_seconds() + 1)


async def main():
    manager = LyricManager()
    await asyncio.gather(spotify_watcher(manager=manager), lyric_loop(manager=manager))

asyncio.run(main())